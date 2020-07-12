"""
Common code for HUD view elements.
"""
import datetime
import math
import threading

import pygame

import views.utils as utils
from common_utils import task_timer, units
from configuration import configuration
from data_sources import traffic
from rendering import colors, display

DEFAULT_FONT = "./assets/fonts/LiberationMono-Bold.ttf"

SIN_RADIANS_BY_DEGREES = {}
COS_RADIANS_BY_DEGREES = {}

max_target_bugs = 25
imperial_occlude = units.yards_to_sm * 10
imperial_faraway = units.yards_to_sm * 5
imperial_superclose = units.yards_to_sm / 8.0

# Fill the quick trig look up tables.
for degrees in range(-360, 361):
    radians = math.radians(degrees)
    SIN_RADIANS_BY_DEGREES[degrees] = math.sin(radians)
    COS_RADIANS_BY_DEGREES[degrees] = math.cos(radians)


def get_reticle_size(
    distance: float,
    min_reticle_size: float = 0.05,
    max_reticle_size: float = 0.20
) -> float:
    """
    The the size of the reticle based on the distance of the target.

    Arguments:
        distance {float} -- The distance (feet) to the target.

    Keyword Arguments:
        min_reticle_size {float} -- The minimum size of the reticle. (default: {0.05})
        max_reticle_size {float} -- The maximum size of the reticle. (default: {0.20})

    Returns:
        float -- The size of the reticle (in proportion to the screen size.)
    """

    if distance <= imperial_superclose:
        on_screen_reticle_scale = max_reticle_size
    elif distance >= imperial_faraway:
        on_screen_reticle_scale = min_reticle_size
    else:
        delta = distance - imperial_superclose
        scale_distance = imperial_faraway - imperial_superclose
        ratio = delta / scale_distance
        reticle_range = max_reticle_size - min_reticle_size

        on_screen_reticle_scale = min_reticle_size + \
            (reticle_range * (1.0 - ratio))

    return on_screen_reticle_scale


def get_heading_bug_x(
    heading: float,
    bearing: float,
    degrees_per_pixel: float
) -> int:
    """
    Gets the X position of a heading bug. 0 is the LHS.

    Arguments:
        heading {float} -- The current heading of the plane
        bearing {float} -- The bearing of the target.
        degrees_per_pixel {float} -- The number of degrees per horizontal pixel.

    Returns:
        int -- The screen X position.
    """

    delta = (bearing - heading + 180)
    if delta < 0:
        delta += 360

    if delta > 360:
        delta -= 360

    return int(delta * degrees_per_pixel)


def get_onscreen_traffic_projection__(
    heading: float,
    pitch: float,
    roll: float,
    bearing: float,
    distance: float,
    altitude_delta: float,
    pixels_per_degree: float
):
    """
    Attempts to figure out where the traffic reticle should be rendered.
    Returns value RELATIVE to the screen center.
    """

    # Assumes traffic.position_valid
    # TODO - Account for aircraft roll...
    slope = altitude_delta / distance
    vertical_degrees_to_target = math.degrees(math.atan(slope))
    vertical_degrees_to_target -= pitch

    # TODO - Double check ALL of this math...
    horizontal_degrees_to_target = bearing - heading

    screen_y = -vertical_degrees_to_target * pixels_per_degree
    screen_x = horizontal_degrees_to_target * pixels_per_degree

    return screen_x, screen_y


def run_ahrs_hud_element(
    element_type,
    use_detail_font: bool = True
):
    """
    Runs an AHRS based HUD element alone for testing purposes

    Arguments:
        element_type {type} -- The class to create.

    Keyword Arguments:
        use_detail_font {bool} -- Should the detail font be used. (default: {True})
    """

    from data_sources import ahrs_simulation
    from datetime import datetime

    clock = pygame.time.Clock()

    __backpage_framebuffer__, screen_size = display.display_init()  # args.debug)
    __width__, __height__ = screen_size
    pygame.mouse.set_visible(False)

    pygame.font.init()

    font_size_std = int(__height__ / 10.0)
    font_size_detail = int(__height__ / 12.0)

    __font__ = pygame.font.Font(DEFAULT_FONT, font_size_std)
    __detail_font__ = pygame.font.Font(DEFAULT_FONT, font_size_detail)

    if use_detail_font:
        font = __detail_font__
    else:
        font = __font__

    __aircraft__ = ahrs_simulation.AhrsSimulation()

    __pixels_per_degree_y__ = (__height__ / configuration.CONFIGURATION.get_degrees_of_pitch()
                               ) * configuration.CONFIGURATION.get_pitch_degrees_display_scaler()

    hud_element = element_type(
        configuration.CONFIGURATION.get_degrees_of_pitch(),
        __pixels_per_degree_y__,
        font,
        (__width__, __height__))

    while True:
        orientation = __aircraft__.get_ahrs()
        orientation.utc_time = str(datetime.utcnow())
        __aircraft__.simulate()
        __backpage_framebuffer__.fill(colors.BLACK)
        hud_element.render(__backpage_framebuffer__, orientation)
        pygame.display.flip()
        clock.tick(60)


def run_adsb_hud_element(
    element_type,
    use_detail_font: bool = True
):
    """
    Runs a ADSB based HUD element alone for testing purposes

    Arguments:
        element_type {type} -- The class to create.

    Keyword Arguments:
        use_detail_font {bool} -- Should the detail font be used. (default: {True})
    """

    from data_sources import ahrs_simulation, traffic
    from data_sources.data_cache import HudDataCache

    simulated_traffic = (traffic.SimulatedTraffic(),
                         traffic.SimulatedTraffic(),
                         traffic.SimulatedTraffic())

    clock = pygame.time.Clock()

    __backpage_framebuffer__, screen_size = display.display_init()  # args.debug)
    __width__, __height__ = screen_size
    pygame.mouse.set_visible(False)

    pygame.font.init()

    font_size_std = int(__height__ / 10.0)
    font_size_detail = int(__height__ / 12.0)

    __font__ = pygame.font.Font(DEFAULT_FONT, font_size_std)
    __detail_font__ = pygame.font.Font(DEFAULT_FONT, font_size_detail)

    if use_detail_font:
        font = __detail_font__
    else:
        font = __font__

    __aircraft__ = ahrs_simulation.AhrsSimulation()

    __pixels_per_degree_y__ = (__height__ / configuration.CONFIGURATION.get_degrees_of_pitch()) * \
        configuration.CONFIGURATION.get_pitch_degrees_display_scaler()

    hud_element = element_type(
        configuration.CONFIGURATION.get_degrees_of_pitch(),
        __pixels_per_degree_y__,
        font,
        (__width__, __height__))

    while True:
        for test_data in simulated_traffic:
            test_data.simulate()
            traffic.AdsbTrafficClient.TRAFFIC_MANAGER.handle_traffic_report(
                test_data.icao_address,
                test_data.to_json())

        HudDataCache.purge_old_textures()
        orientation = __aircraft__.get_ahrs()
        __aircraft__.simulate()
        __backpage_framebuffer__.fill(colors.BLACK)
        hud_element.render(__backpage_framebuffer__, orientation)
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    for distance in range(0, int(2.5 * units.yards_to_sm), int(units.yards_to_sm / 10.0)):
        print("{0}' -> {1}".format(distance, get_reticle_size(distance)))

    heading = 327
    pitch = 0
    roll = 0
    distance = 1000
    altitude_delta = 1000
    pixels_per_degree = 10
    for bearing in range(0, 360, 10):
        print("Bearing {0} -> {1}px".format(bearing,
                                            get_heading_bug_x(heading, bearing, 2.2222222)))
        x, y = get_onscreen_traffic_projection__(
            heading, pitch, roll, bearing, distance, altitude_delta, pixels_per_degree)
        print("    {0}, {1}".format(x + 400, y + 240))
        print("TRUE: {0} -> {1} MAG".format(bearing,
                                            utils.apply_declination(bearing)))