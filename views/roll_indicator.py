import math

import pygame
from data_sources.ahrs_data import AhrsData
from rendering import colors

from views.ahrs_element import AhrsElement


class RollIndicatorText(AhrsElement):
    def __init__(
        self,
        degrees_of_pitch: float,
        pixels_per_degree_y: float,
        font,
        framebuffer_size
    ):
        super().__init__(font, framebuffer_size)

        self.__roll_elements__ = {}
        self.__text_y_pos__ = self.__center_y__ - self.__font_half_height__

        for reference_angle in range(-180, 181):
            text = font.render(
                "{0:3}".format(int(math.fabs(reference_angle))),
                True,
                colors.WHITE,
                colors.BLACK)
            size_x, size_y = text.get_size()
            self.__roll_elements__[reference_angle] = (
                text, (size_x >> 1, size_y >> 1))

    def render(
        self,
        framebuffer,
        orientation: AhrsData
    ):
        roll = int(orientation.roll)
        pitch = int(orientation.pitch)
        pitch_direction = ''
        if pitch > 0:
            pitch_direction = '+'
        attitude_text = "{0}{1:3} | {2:3}".format(pitch_direction, pitch, roll)

        roll_texture = self.__font__.render(
            attitude_text,
            True,
            colors.BLACK,
            colors.WHITE)
        texture_size = roll_texture.get_size()
        text_half_width, text_half_height = texture_size
        text_half_width = text_half_width >> 1
        framebuffer.blit(
            roll_texture,
            (self.__center_x__ - text_half_width, self.__text_y_pos__))


class RollIndicator(AhrsElement):
    def __init__(
        self,
        degrees_of_pitch: float,
        pixels_per_degree_y: float,
        font,
        framebuffer_size
    ):
        super().__init__(font, framebuffer_size)

        self.__text_y_pos__ = self.__center_y__ - self.__font_half_height__
        self.arc_radius = int(framebuffer_size[1] / 3)
        self.top_arc_squash = 0.75
        self.arc_angle_adjust = math.pi / 8.0
        self.roll_indicator_arc_radians = 0.03
        self.arc_box = [
            self.__center_x__ - self.arc_radius,
            self.__center_y__ - (self.arc_radius >> 1),
            self.arc_radius << 1,
            (self.arc_radius << 1) * self.top_arc_squash]
        self.reference_line_size = self.__line_width__ * 5
        self.reference_arc_box = [self.arc_box[0],
                                  self.arc_box[1] - self.reference_line_size,
                                  self.arc_box[2],
                                  self.arc_box[3] - self.reference_line_size]
        self.smaller_reference_arc_box = [self.arc_box[0],
                                          self.arc_box[1] -
                                          (self.reference_line_size >> 1),
                                          self.arc_box[2],
                                          self.arc_box[3] - (self.reference_line_size >> 1)]
        self.half_pi = math.pi / 2.0

    def render(
        self,
        framebuffer,
        orientation: AhrsData
    ):
        roll_in_radians = math.radians(orientation.roll)

        # Draws the reference arc
        pygame.draw.arc(
            framebuffer,
            colors.GREEN,
            self.arc_box,
            self.arc_angle_adjust,
            math.pi - self.arc_angle_adjust,
            self.__line_width__)

        # Draw the important reference angles
        for roll_angle in [-30, -15, 15, 30]:
            reference_roll_in_radians = math.radians(roll_angle + 90.0)
            pygame.draw.arc(
                framebuffer,
                colors.GREEN,
                self.smaller_reference_arc_box,
                reference_roll_in_radians - self.roll_indicator_arc_radians,
                reference_roll_in_radians + self.roll_indicator_arc_radians,
                (self.reference_line_size >> 1))

        # Draw the REALLY important reference angles longer
        for roll_angle in [-90, -60, -45, 0, 45, 60, 90]:
            reference_roll_in_radians = math.radians(roll_angle + 90.0)
            pygame.draw.arc(
                framebuffer,
                colors.GREEN,
                self.reference_arc_box,
                reference_roll_in_radians - self.roll_indicator_arc_radians,
                reference_roll_in_radians + self.roll_indicator_arc_radians,
                self.reference_line_size)

        # Draws the current roll
        pygame.draw.arc(
            framebuffer,
            colors.YELLOW,
            self.arc_box,
            self.half_pi - roll_in_radians - self.roll_indicator_arc_radians,
            self.half_pi - roll_in_radians + self.roll_indicator_arc_radians,
            self.reference_line_size * 2)


if __name__ == '__main__':
    from views.hud_elements import run_ahrs_hud_element
    run_ahrs_hud_element(RollIndicator, False)
