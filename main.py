# Heartbeat LED array on Raspberry Pi Pico
# Wiring:
#   GP15 -> 1kΩ -> 2N2222 base
#   emitter -> GND
#   collector -> LED cathodes
#   LED anodes -> 100Ω -> VCC
#
# Brightness and timing values were tuned by eye to feel natural.

# This project runs on MicroPython (not standard Python).
# 'machine' provides direct access to Pico hardware (GPIO, PWM),
#  and 'utime' is used for millisecond-level timing control.

import machine, utime

PWM_PIN   = 15        # GPIO physically routed to the transistor base
PWM_FREQ  = 1200      # High enough to avoid visible flicker
MAX_LEVEL = 0.95      # Limits peak brightness to save batteries and LED lifetime
GAMMA     = 2.2       # Standard perceptual gamma correction

# Heartbeat timing parameters (milliseconds)
BPM       = 45        # Slow, calm heartbeat
UP1_MS    = 160       # First beat: fast rise
DOWN1_MS  = 410       # Long, soft decay
GAP_MS    = 340       # Short pause between the two beats
UP2_MS    = 140       # Second beat: slightly quicker and weaker
DOWN2_MS  = 270
PEAK1     = 0.95      # Peak brightness of first beat
PEAK2     = 0.65      # Peak brightness of second beat

pwm = machine.PWM(machine.Pin(PWM_PIN))
pwm.freq(PWM_FREQ)

def set_level(level: float):
    """
    Set LED brightness using PWM.
    The value is gamma-corrected to better match human perception.
    """
    level = max(0.0, min(1.0, level))
    pwm.duty_u16(int(((level * MAX_LEVEL) ** GAMMA) * 65535))

def ease_in_out_cubic(t: float) -> float:
    """
    Cubic ease-in / ease-out function.

    Instead of changing brightness linearly, this curve starts slowly,
    accelerates in the middle, and slows down again at the end.
    This makes fades feel more organic and less mechanical.
    """
    return 4*t*t*t if t < 0.5 else 1 - pow(-2*t + 2, 3)/2

def ramp(start, end, duration_ms, steps=90):
    """
    Smoothly ramp brightness from 'start' to 'end' over a given time.

    The transition is split into small steps and shaped using
    the cubic easing function for a natural-looking fade.
    """
    if steps < 1: 
        steps = 1

    step_delay = max(1, int(duration_ms / steps))

    for i in range(steps + 1):
        t = i / steps
        eased = ease_in_out_cubic(t)
        set_level(start + (end - start) * eased)
        utime.sleep_ms(step_delay)


def heartbeat_cycle():
    """
    One complete heartbeat cycle:
    fast first beat, short pause, softer second beat, then rest.
    """
    cycle_ms = int(60000 / BPM)
    # First beat
    ramp(0.0, PEAK1, UP1_MS)
    ramp(PEAK1, 0.0, DOWN1_MS)

    #Pause between beats
    utime.sleep_ms(GAP_MS)

    #Second beat
    ramp(0.0, PEAK2, UP2_MS)
    ramp(PEAK2, 0.0, DOWN2_MS)

    # Rest until next cycle to maintain BPM
    used = UP1_MS + DOWN1_MS + GAP_MS + UP2_MS + DOWN2_MS
    rest = max(0, cycle_ms - used)
    if rest:
        utime.sleep_ms(rest)

try:
    set_level(0.0)
    while True:
        heartbeat_cycle()
except KeyboardInterrupt:
    pass
finally:
    set_level(0.0)
    pwm.deinit()
