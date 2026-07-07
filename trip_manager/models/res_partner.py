# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    """Extends res.partner with tour guide profile"""
    
    _inherit = 'res.partner'
    _description = 'Tour Guide Profile'

    # ------------------------------------------------------------------------------
    #   MARK: FIELDS
    # ------------------------------------------------------------------------------
    is_guide = fields.Boolean(string='Is Guide', default=False)
    experience_years = fields.Integer(string='Experience (Years)')
    spoken_language = fields.Char(string='Languages Spoken')
    specialization = fields.Selection([
        ('heritage',   'Heritage & Culture'),
        ('adventure',  'Adventure & Trekking'),
        ('pilgrimage', 'Pilgrimage'),
        ('wildlife',   'Wildlife & Nature'),
        ('general',    'General'),
    ], string='Specialization', default='general')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    charge_per_day = fields.Monetary(string='Service Charge',  currency_field='currency_id')
    city_ids = fields.Many2many('trip.manager.city', string='Serviceable Cities')