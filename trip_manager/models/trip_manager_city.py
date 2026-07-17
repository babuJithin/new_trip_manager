# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerCity(models.Model):
    """Stores master records for travel cities used to group destinations,
    hotels, and guides by geographic location."""
    
    _name = 'trip.manager.city'
    _description = 'A central registry of cities'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='City', required=True )
