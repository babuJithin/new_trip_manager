# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerDestinationCategory(models.Model):
    """Stores master category records for destination location types
    such as Beach, Hill Station, Heritage Site, or Wildlife Reserve."""
    
    _name = 'trip.manager.destination.category'
    _description = 'A central registry of destination location type'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Destination Category', required=True )
