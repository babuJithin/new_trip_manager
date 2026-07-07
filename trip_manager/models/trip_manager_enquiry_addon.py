# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TripManagerEnquiryAddon(models.Model):
    """Represents a single inclusion or exclusion line for a customer enquiry option,
    capturing additional services such as entry tickets, guides, flights, or boat rides
    along with their associated cost."""

    _name = 'trip.manager.enquiry.addon'
    _description = 'Enquiry Add-on Line'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    description = fields.Char(string='Description')
    is_guide_category = fields.Boolean(related='category_id.is_guide_category', store=False)
    cost = fields.Monetary(string='Cost', currency_field='currency_id')    
    
    category_id = fields.Many2one('trip.manager.addon.category', string='Category')
    currency_id = fields.Many2one('res.currency', related='enquiry_id.currency_id')
    guide_id = fields.Many2one('res.partner', domain=[('is_guide', '=', True)])    
    option_id = fields.Many2one('trip.manager.enquiry.option',
                                required=True, ondelete='cascade')
    enquiry_id = fields.Many2one('trip.manager.enquiry',
                                related='option_id.enquiry_id',
                                store=True, string='Enquiry')

    # ------------------------------------------------------------------------------
    #   MARK: COMPUTE/OVERRIDDEN METHODS
    # ------------------------------------------------------------------------------
    @api.onchange('guide_id')
    def _onchange_guide_id(self):
        """Auto-fills the cost from the selected guide's daily charge rate,
        saving the user from entering it manually."""
        
        if self.guide_id:
            self.cost = self.guide_id.charge_per_day
            
    @api.onchange('category_id')
    def _onchange_category_id(self):
        """Clears the guide selection when the category is changed to a
        non-guide category, preventing stale guide data from carrying over."""
        
        if not self.category_id.is_guide_category:
            self.guide_id = False
            
