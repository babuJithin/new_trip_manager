# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TripManagerCity(models.Model):
    """Stores master records for travel cities used to group destinations,
    hotels, and guides by geographic location."""
    
    _name = 'trip.manager.city'
    _description = 'A central registry of cities'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    name = fields.Char(string='City', required=True )
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', 
                                             domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    
    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.onchange('state_id')
    def _onchange_state_id(self):
        """Auto fills country when a state is given"""
        
        if self.state_id:
            self.country_id = self.state_id.country_id
            
    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clears state if it does not belong to the selected country"""
        
        if self.state_id and self.state_id.country_id != self.country_id:
            self.state_id = False