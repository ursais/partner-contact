# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import common


class TestResPartner(common.TransactionCase):
    def setUp(self):
        super(TestResPartner, self).setUp()
        self.dea_category_id = self.env.ref(
            "partner_identification_dea.res_partner_id_category_dea",
            raise_if_not_found=False,
        )
        self.medical_id = self.env.ref(
            "partner_identification_dea.res_partner_id_category_medical",
            raise_if_not_found=False,
        )
        self.controlled_id = self.env.ref(
            "partner_identification_dea.res_partner_id_category_controlled_substance",
            raise_if_not_found=False,
        )
        self.date = fields.Date.today() + relativedelta(days=30)
        self.expired_date = fields.Date.today() - relativedelta(days=10)
        self.partner_obj = self.env["res.partner"]
        self.partner_number_obj = self.env["res.partner.id_number"]
        self.partner_roy = self.partner_obj.create({"name": "Roy"})
        self.partner_jimmy = self.partner_obj.create({"name": "Jimmy"})
        self.partner_john = self.partner_obj.create({"name": "John"})
        self.partner_number_obj.create(
            {
                "partner_id": self.partner_roy.id,
                "category_id": self.dea_category_id.id,
                "status": "open",
                "valid_until": self.date,
                "name": "AA1270533",
            }
        )
        self.partner_number_obj.create(
            {
                "partner_id": self.partner_jimmy.id,
                "category_id": self.medical_id.id,
                "status": "open",
                "valid_until": self.date,
                "name": "12360001",
            }
        )
        self.controlled_number = self.partner_number_obj.create(
            {
                "partner_id": self.partner_john.id,
                "category_id": self.controlled_id.id,
                "status": "open",
                "valid_until": self.date,
                "name": "78901234",
            }
        )

    def test_dea_and_medical_license_fields_computed(self):
        """Test DEA and medical license fields computed from ID numbers."""
        self.partner_roy.invalidate_cache()
        self.partner_jimmy.invalidate_cache()
        self.assertEqual(self.partner_roy.dea_number, "AA1270533")
        self.assertEqual(self.partner_roy.dea_expired_date, self.date)
        self.assertEqual(self.partner_jimmy.medical_license, "12360001")
        self.assertEqual(self.partner_jimmy.medical_license_expired_date, self.date)

    def test_contr_subst_license_fields_computed(self):
        """Test controlled substance license fields computed from ID number."""
        self.partner_john.invalidate_cache()
        self.assertEqual(self.partner_john.contr_subst_license, "78901234")
        self.assertEqual(self.partner_john.contr_subst_expired_date, self.date)

    def test_contr_subst_license_expired_or_inactive(self):
        """Test license is ignored if expired or inactive."""
        # Test with status = 'closed'
        self.controlled_number.status = 'close'
        self.partner_john._compute_dea_medical_license()
        self.assertEqual(self.partner_john.contr_subst_license, "")
        self.assertFalse(self.partner_john.contr_subst_expired_date)
        # Test with future status=open but expired date
        self.controlled_number.write({
            'status': 'open',
            'valid_until': self.expired_date,
        })
        self.partner_john._compute_dea_medical_license()
        self.assertEqual(self.partner_john.contr_subst_license, "78901234")
        self.assertEqual(self.partner_john.contr_subst_expired_date, self.expired_date)

    def test_name_search_by_contr_subst_license(self):
        """Test name_search can find partner by controlled substance license."""
        result = self.partner_obj.name_search(name="78901234")
        self.assertTrue(result)
        self.assertEqual(result[0][0], self.partner_john.id)
        self.assertIn("John", result[0][1])

    def test_send_expiration_date_notification(self):
        self.partner_obj.send_expiration_date_notification()
