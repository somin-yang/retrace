"""Build-time audio only. The game itself needs just pygame and these files.

Original Glass Echo B arrangement and original effects for RE:TRACE.
Instrument timbres: TimGM6mb, used through FluidSynth (credits bundled).
Development requirements: numpy, scipy, libfluidsynth and ffmpeg.
"""
from pathlib import Path
import ctypes as C
import ctypes.util
import json
import subprocess
import wave
import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
RATE = 44100
BANK = Path(__file__).resolve().parent / 'TimGM6mb.sf2'
metrics = {}
lib = C.CDLL(ctypes.util.find_library('fluidsynth'))
P = C.c_void_p
signatures = {
    'new_fluid_settings': ([], P),
    'fluid_settings_setnum': ([P, C.c_char_p, C.c_double], C.c_int),
    'fluid_settings_setint': ([P, C.c_char_p, C.c_int], C.c_int),
    'new_fluid_synth': ([P], P),
    'fluid_synth_sfload': ([P, C.c_char_p, C.c_int], C.c_int),
    'fluid_synth_program_change': ([P, C.c_int, C.c_int], C.c_int),
    'fluid_synth_cc': ([P, C.c_int, C.c_int, C.c_int], C.c_int),
    'fluid_synth_noteon': ([P, C.c_int, C.c_int, C.c_int], C.c_int),
    'fluid_synth_noteoff': ([P, C.c_int, C.c_int], C.c_int),
    'fluid_synth_write_float': ([P, C.c_int, P, C.c_int, C.c_int, P, C.c_int, C.c_int], C.c_int),
    'delete_fluid_synth': ([P], None), 'delete_fluid_settings': ([P], None),
}
for name, (args, result) in signatures.items():
    getattr(lib, name).argtypes = args
    getattr(lib, name).restype = result


def save(name, data, ogg=False):
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 1:
        data = np.column_stack((data, data))
    assert np.isfinite(data).all() and np.max(np.abs(data)) < .95
    path = OUT / (name + '.wav')
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(np.rint(data * 32767).astype('<i2').tobytes())
    metrics[name] = {'seconds': len(data) / RATE,
                     'peak': float(np.max(np.abs(data))),
                     'rms': float(np.sqrt(np.mean(data ** 2))),
                     'loop_jump': float(np.max(np.abs(data[-1] - data[0])))}
    if ogg:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                        '-i', str(path), '-c:a', 'libvorbis', '-q:a', '5',
                        str(path.with_suffix('.ogg'))], check=True)
        path.unlink()
    print('Rendered', name, metrics[name], flush=True)


def note(notes, beat, pitch, length, velocity, channel=0):
    notes.append((beat, pitch, length, velocity, channel))


def render_loop(notes, bpm, beats, programs):
    beat_time = 60 / bpm
    period = round(beats * beat_time * RATE)
    settings = lib.new_fluid_settings()
    lib.fluid_settings_setnum(settings, b'synth.sample-rate', RATE)
    lib.fluid_settings_setnum(settings, b'synth.gain', .55)
    lib.fluid_settings_setint(settings, b'synth.chorus.active', 0)
    lib.fluid_settings_setint(settings, b'synth.reverb.active', 1)
    synth = lib.new_fluid_synth(settings)
    try:
        assert lib.fluid_synth_sfload(synth, str(BANK).encode(), 1) >= 0
        for channel, program in programs.items():
            lib.fluid_synth_program_change(synth, channel, program)
            lib.fluid_synth_cc(synth, channel, 10, {0:42, 1:54, 2:85, 3:64}[channel])
            lib.fluid_synth_cc(synth, channel, 91, 40 if channel == 0 else 52)
        events = []
        # Warm up a complete repeat so the exported second cycle has reverb tails
        # from the preceding cycle. There is no silent fade-out at the loop point.
        for repeat in range(3):
            for beat, pitch, length, velocity, channel in notes:
                start = repeat * period + round((beat % beats) * beat_time * RATE)
                end = start + round(length * beat_time * RATE)
                events += [(start, 1, channel, pitch, velocity), (end, 0, channel, pitch, 0)]
        events.sort()
        left = np.zeros(period * 3, dtype=np.float32)
        right = np.zeros_like(left)
        current = 0
        for frame, on, channel, pitch, velocity in events + [(len(left), -1, 0, 0, 0)]:
            frame = min(len(left), frame)
            if frame > current:
                assert lib.fluid_synth_write_float(synth, frame-current, P(left.ctypes.data),
                    current, 1, P(right.ctypes.data), current, 1) == 0
                current = frame
            if on == 1:
                lib.fluid_synth_noteon(synth, channel, pitch, velocity)
            elif on == 0:
                lib.fluid_synth_noteoff(synth, channel, pitch)
        audio = np.column_stack((left[period:period*2], right[period:period*2]))
        # Remove DC bias, preserve dynamics, normalize the master, mix quietly in game.
        audio -= np.mean(audio, axis=0)
        audio *= min(.30 / np.max(np.abs(audio)), .055 / np.sqrt(np.mean(audio**2)))
        # A ten-millisecond edge taper removes phase clicks from sampled
        # instruments/reverb. Musical tails remain; there is no seconds-long gap.
        edge = round(.01 * RATE)
        ramp = np.sin(np.linspace(0, np.pi/2, edge))**2
        audio[:edge] *= ramp[:, None]
        audio[-edge:] *= ramp[::-1, None]
        return audio
    finally:
        lib.delete_fluid_synth(synth); lib.delete_fluid_settings(settings)


# Basement: four eight-bar sections, preserving the selected B melody and echoes.
patterns = [[(.5,74),(2,69),(3,72)],[(.5,65),(2.5,69)],
            [(.5,74),(2,77),(3,76)],[(.5,72),(2.5,69)],
            [(.5,70),(2,74),(3,69)],[(.5,67),(2.5,65)],
            [(.5,69),(2,73),(3,76)],[(.5,74),(2.5,69)]]
chords = [(50,[57,62,65]),(46,[53,57,62]),(43,[50,58,62]),(45,[52,55,62])]
basement = []
for bar in range(32):
    section, local = divmod(bar, 8)
    bass, voicing = chords[(local//2) % 4]
    for i, pitch in enumerate((bass+12, voicing[0], voicing[-1])):
        note(basement, bar*4+i*.035, pitch, 3.8, 28-i%2*3, 1)
    for j, (offset, pitch) in enumerate(patterns[local]):
        if section == 1 and j == 2 or section == 3 and local in (1,5) and j == 1:
            continue  # Breathing room; the tune should not compete with the puzzle.
        if section == 2 and local in (1,3,5):
            pitch += 12
        at = bar*4+offset
        note(basement, at, pitch, .8, 48 if section < 2 else 43)
        note(basement, at+.78, pitch, .65, 21, 2)
        note(basement, at+1.56, pitch, .6, 12, 2)
music = render_loop(basement, 64, 128, {0:10,1:4,2:10})
save('glass_echo', music, True)
# Same length and phase, gently low-passed for the enclosed elevator mix.
filter_ = butter(2, 1300, fs=RATE, output='sos')
warm = np.concatenate((music[-RATE*2:], music))
muffled = sosfilt(filter_, warm, axis=0)[RATE*2:]
save('glass_echo_lift', muffled, True)

# Surface: same motif resolved into D major, warmer piano and more forward motion.
surface = []
major_chords = [(50,[57,62,66]),(47,[54,59,62]),(43,[50,55,59]),(45,[52,57,61])]
for bar in range(24):
    root, harmony = major_chords[(bar//2) % 4]
    base = bar*4
    note(surface, base, root, 3.5, 39, 1)
    for j, pitch in enumerate(harmony*2):
        note(surface, base+.25+j*.5, pitch+(12 if j >= 3 else 0), 1.5, 37, 1)
    for i, pitch in enumerate(harmony):
        note(surface, base+i*.02, pitch, 3.8, 20, 3)
    for offset, pitch in patterns[bar % 8]:
        if pitch % 12 in (0,5,10):
            pitch += 1  # C/F/B-flat become C-sharp/F-sharp/B.
        note(surface, base+offset, pitch, 1.2, 52)
        note(surface, base+offset+.85, pitch, .75, 16, 2)
save('surface_release', render_loop(surface, 80, 96, {0:10,1:0,2:10,3:48}), True)

# Quiet indoor machinery: tonal electrical hum, absolutely no wind/noise layer.
t = np.arange(RATE*32)/RATE
hum = (.024*np.sin(2*np.pi*60*t) + .009*np.sin(2*np.pi*120*t)
       + .004*np.sin(2*np.pi*180*t)) * (.92+.08*np.cos(2*np.pi*t/16))
save('facility_hum', hum)


def tone(t, hz, length, gain=1):
    env = np.minimum(1, t/.008)*np.maximum(0,1-t/length)**1.8
    return gain*env*(np.sin(2*np.pi*hz*t)+.12*np.sin(2*np.pi*hz*2*t))


def phrase(pitches, spacing, duration, gain=.11):
    data = np.zeros(round(RATE*(spacing*(len(pitches)-1)+duration+.03)))
    for i, hz in enumerate(pitches):
        begin = round(i*spacing*RATE)
        tt = np.arange(round(duration*RATE))/RATE
        data[begin:begin+len(tt)] += tone(tt, hz, duration, gain)
    return data


def effect(name, length):
    t = np.arange(round(length*RATE))/RATE
    rng = np.random.default_rng(821)
    noise = rng.uniform(-1,1,len(t))
    return t, noise


t,n = effect('lever',.20)
lever = .13*np.sin(2*np.pi*(180*t-200*t*t))*np.exp(-t*32)
lever += .055*n*np.exp(-t*90) + .06*np.sin(2*np.pi*85*t)*np.exp(-t*19)
save('sfx_lever', lever*np.minimum(1,t/.002))
# Automatic power reset follows the detector beep; identical family timbre.
save('sfx_lever_reset', np.concatenate((np.zeros(round(RATE*.075)),
                                      lever*np.minimum(1,t/.002))))
t,n = effect('button',.15)
button = .06*n*np.exp(-t*180) + tone(np.maximum(0,t-.018),730,.12,.085)*(t>=.018)
save('sfx_button', button*np.minimum(1,t/.001))
t,n = effect('mirror',.30)
envelope = np.sin(np.pi*np.minimum(1,t/.30))**.8
mirror = .07*(np.sin(2*np.pi*(230*t+90*t*t))+.22*np.sin(2*np.pi*510*t))*envelope
mirror += .05*n*np.exp(-np.abs(t-.268)*220)
save('sfx_mirror', mirror)
save('sfx_panel', phrase([580,870],.095,.15,.085))
save('sfx_shutdown', phrase([790,565,335],.13,.22,.11))
save('sfx_start', phrase([440,660,880],.11,.30,.12))
t,n = effect('sputter',.12)
envelope = np.exp(-t*36)*np.minimum(1,t/.003)
noise = sosfilt(butter(1,2200,fs=RATE,output='sos'),n)
save('sfx_sputter', .05*noise*envelope+.025*np.sin(2*np.pi*1750*t)*envelope)
save('sfx_failure', phrase([310,195],.12,.22,.10))
(ROOT/'audio_source/audio_metrics.json').write_text(json.dumps(metrics,indent=2))
(ROOT/'audio_source/music_scores.json').write_text(json.dumps({'basement':basement,'surface':surface},indent=2))
