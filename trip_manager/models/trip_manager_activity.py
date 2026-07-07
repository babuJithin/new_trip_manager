# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerActivity(models.Model):
    """Stores master records for travel activities available at destinations,
    such as Trekking, Boating, Elephant Ride, or Spice Garden Visit."""   
     
    _name = 'trip.manager.activity'
    _description = 'A central registry of trip activities'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Activity', required=True )
