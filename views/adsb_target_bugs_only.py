import pygame
from common_utils.task_timer import TaskTimer
from data_sources.ahrs_data import AhrsData
from data_sources.data_cache import HudDataCache
from data_sources.traffic import Traffic
from rendering import colors

from views import utils
from views.adsb_element import AdsbElement
from views.hud_elements import (get_heading_bug_x, get_reticle_size,
                                max_target_bugs)


class AdsbTargetBugsOnly(AdsbElement):
    def __init__(
        self,
        degrees_of_pitch: float,
        pixels_per_degree_y: float,
        font,
        framebuffer_size
    ):
        AdsbElement.__init__(
            self, degrees_of_pitch, pixels_per_degree_y, font, framebuffer_size)

        self.task_timer = TaskTimer('AdsbTargetBugs')
        self.__listing_text_start_y__ = int(self.__font__.get_height() * 4)
        self.__listing_text_start_x__ = int(
            self.__framebuffer_size__[0] * 0.01)
        self.__next_line_distance__ = int(font.get_height() * 1.5)
        self.__top_border__ = 0
        self.__bottom_border__ = self.__height__ - int(self.__height__ * 0.1)

    def __render_traffic_heading_bug__(
        self,
        traffic_report: Traffic,
        heading: float,
        orientation: AhrsData,
        framebuffer
    ):
        """
        Render a single heading bug to the framebuffer.

        Arguments:
            traffic_report {Traffic} -- The traffic we want to render a bug for.
            heading {int} -- Our current heading.
            orientation {Orientation} -- Our plane's current orientation.
            framebuffer {Framebuffer} -- What we are going to draw to.
        """

        # Render using the Above us bug
        # target_bug_scale = 0.04
        target_bug_scale = get_reticle_size(traffic_report.distance)

        heading_bug_x = get_heading_bug_x(
            heading,
            utils.apply_declination(traffic_report.bearing),
            self.__pixels_per_degree_x__)

        try:
            # TODO
            # Get any avaiable OWNSHIP data to make sure
            # that we are comparing pressure altitude to pressure altitude....
            # .. or use the Pressure Alt if that is available from the avionics.
            # .. or just validate that we are using pressure altitude...
            is_below = (orientation.alt - 100) > traffic_report.altitude
            reticle, reticle_edge_position_y = self.get_below_reticle(
                heading_bug_x, target_bug_scale) if is_below else self.get_above_reticle(heading_bug_x, target_bug_scale)

            bug_color = colors.BLUE if traffic_report.is_on_ground() == True else colors.RED

            pygame.draw.polygon(framebuffer, bug_color, reticle)
        except Exception:
            pass

    def render(
        self,
        framebuffer,
        orientation: AhrsData
    ):
        # Render a heading strip along the top

        self.task_timer.start()
        heading = orientation.get_onscreen_projection_heading()

        # Get the traffic, and bail out of we have none
        traffic_reports = HudDataCache.get_reliable_traffic()

        if traffic_reports is None:
            self.task_timer.stop()
            return

        reports_to_show = traffic_reports[:max_target_bugs]

        if not isinstance(heading, str):
            [self.__render_traffic_heading_bug__(
                traffic_report,
                heading,
                orientation,
                framebuffer) for traffic_report in reports_to_show]

        self.task_timer.stop()


if __name__ == '__main__':
    from views.hud_elements import run_adsb_hud_element

    run_adsb_hud_element(AdsbTargetBugsOnly)
