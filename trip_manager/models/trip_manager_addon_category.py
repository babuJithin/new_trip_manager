# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class TripManagerAddonCategory(models.Model):
    """Stores master category records for trip inclusions and exclusions,
    such as Entry Ticket, Guide, Flight, and Boat Ride.
    The is_guide_category flag identifies categories that require
    a guide selection on the enquiry add-on line."""
    
    _name = 'trip.manager.addon.category'
    _description = 'Inclusion/Exclusion Category'
    
    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='Category', required=True)
    is_guide_category = fields.Boolean(string='Is Guide Category', default=False)