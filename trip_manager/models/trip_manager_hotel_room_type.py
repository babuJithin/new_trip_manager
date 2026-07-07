# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerHotelRoomType(models.Model):
    """Stores master records for hotel room types linked to specific hotels,
    capturing room rate and maximum occupancy per room category
    such as Standard Room, Deluxe Room, Suite, or Family Room."""
    
    _name = 'trip.manager.hotel.room.type'
    _description = 'A central registry of available hotel room types'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Name', required=True )
    max_occupancy = fields.Integer(string="Maximum Capacity")
    room_rate = fields.Monetary(string='Room Rate', currency_field='currency_id')

    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    hotel_id = fields.Many2one('trip.manager.hotel', string="Hotel")
    
