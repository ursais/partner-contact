# Copyright 2026 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    owner_company_id = fields.Many2one(
        "res.company",
        string="Owner Company",
        help="Company that owns this contact. This is a soft alternative to company_id "
        "that doesn't enforce access security but allows tracking company belonging.",
        index=True,
    )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """
        Override name_search to prioritize current company contacts unless:
        - Full name match
        - Exact code/ref match
        - Exact email match
        """
        args = args or []

        if not name:
            return super().name_search(name, args, operator, limit)

        # Try exact matches first (bypasses company filtering)
        # Check if search term matches full name, exact code, or exact email
        exact_match_domain = [
            "|",
            "|",
            "|",
            ("name", "=ilike", name),
            ("ref", "=ilike", name),
            ("email", "=ilike", name),
            ("vat", "=ilike", name),
        ]

        # Try exact matches first (bypasses company filtering)
        exact_matches = self._search(exact_match_domain + args, limit=limit)
        if exact_matches:
            return self.browse(exact_matches).name_get()

        # For partial matches, prioritize current company contacts
        company_args = args + [
            "|",
            ("owner_company_id", "=", self.env.company.id),
            ("owner_company_id", "=", False),
        ]
        return super().name_search(name, company_args, operator, limit)
