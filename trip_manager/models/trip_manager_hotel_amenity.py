# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerHotelAmenity(models.Model):
    """Stores master records for hotel amenities available across properties,
    such as Swimming Pool, Free WiFi, Spa, Gym, or Airport Shuttle."""
    
    _name = 'trip.manager.hotel.amenity'
    _description = 'A central registry of amenities provided by hotels'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Amenity', required=True )
