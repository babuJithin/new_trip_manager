# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from __future__ import annotations

from odoo import api, fields, models

import typing
if typing.TYPE_CHECKING:
    from .res_country import Country, CountryState


class TripManagerHotel(models.Model):
    """Stores master records for hotels across travel destinations and cities,
    capturing contact details, address, star rating, room types, check-in/check-out
    times, breakfast availability, extra bed pricing, and serviceable cities
    used for filtering hotels by destination and package category tier."""
    
    _name = 'trip.manager.hotel'
    _description = 'A central registry of hotels'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Hotel Name', required=True )
    image = fields.Image(string="Image", max_width=1024, max_height=1024)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    email = fields.Char(string='Email', required=True)
    phone_number = fields.Char(string='Phone Number', required=True)
    star_rating = fields.Selection([
        ('0', '0 star'),
        ('1', '1 star'),
        ('2', '2 star'),
        ('3', '3 star'),
        ('4', '4 star'),
        ('5', '5 star'),
    ], string='Star Rating')
    extra_bed_available = fields.Boolean(string='Exta Bed Available')
    extra_bed_price = fields.Monetary(string='Extra Bed Price', currency_field='currency_id')
    check_in = fields.Float(string='Check-in Time')
    check_out = fields.Float(string='Check-out Time')
    has_breakfast = fields.Boolean(string='Breakfast')
             
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)   
    state_id: CountryState = fields.Many2one("res.country.state", string='State', ondelete='restrict', 
                                             domain="[('country_id', '=?', country_id)]")
    country_id: Country = fields.Many2one('res.country', string='Country', ondelete='restrict')
    city_ids = fields.Many2many('trip.manager.city', string='Cities')
    room_type_ids = fields.One2many('trip.manager.hotel.room.type', 'hotel_id', string="Room Types")
    
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    def _float_to_ampm(self, value):
        """Converts a float time value to a 12-hour AM/PM string format.
        For example, 14.5 becomes '2:30 PM' and 9.0 becomes '9:00 AM'."""
        
        if not value and value != 0:
            return ''
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        period = 'AM' if hours < 12 else 'PM'
        display_hour = hours % 12 or 12
        return f"{display_hour}:{minutes:02d} {period}"
    
    def _compute_display_name(self):
        """Overrides display name to prefix the hotel name with star emoji icons
        based on the star rating, improving readability in dropdown selections.
        For example, a 3-star hotel displays as '⭐⭐⭐ Hotel Name'."""
        
        star_display = {
            '0': '☆ ',
            '1': '⭐',
            '2': '⭐⭐',
            '3': '⭐⭐⭐',
            '4': '⭐⭐⭐⭐',
            '5': '⭐⭐⭐⭐⭐',
        }
        for rec in self:
            stars = star_display.get(rec.star_rating, '')
            rec.display_name = f"{stars} {rec.name}"
