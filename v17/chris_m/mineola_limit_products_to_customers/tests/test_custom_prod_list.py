from odoo.tests.common import HttpCase
from odoo import exceptions

class TestWebsiteSaleInherit(HttpCase):
    post_install = True
    at_install = False

    def setUp(self):
        super(TestWebsiteSaleInherit, self).setUp()

        self.website = self.env['website'].create({
            'name': 'Test Website',
            'domain': 'test.example.com',
        })

        self.product_template1 = self.env['product.template'].create({
            'name': 'Test Product 1',
            'list_price': 100.0,
            'website_published': True,
            'sale_ok': True,
        })

        self.product_template2 = self.env['product.template'].create({
            'name': 'Test Product 2',
            'list_price': 200.0,
            'website_published': True,
            'sale_ok': True,
        })

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })

        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test_user@example.com',
            'partner_id': self.partner.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })

        self.custom_prod_list = self.env['custom.prod.list'].create({
            'name': 'Test Custom Product List',
            'product_ids': [(4, self.product_template1.id)],
            'partner_ids': [(4, self.partner.id)],
            'active': True,
        })
        
        self.partner.write({
            'custom_prod_list_id': self.custom_prod_list.id,
        })

    def test_01_product_search_in_website(self):
        self.authenticate('test_user', 'test_user')
        self.assertEqual(self.user.partner_id, self.partner)
        self.assertEqual(self.partner.custom_prod_list_id, self.custom_prod_list)

        # Ensure that when we search the products as this user, 
        # we get only the products from the custom list
        domain = [("id", "in", self.partner.custom_prod_list_id.product_ids.ids),
                  ('is_published', '=', True), ('sale_ok', '=', True)]
        products = self.env['product.template'].sudo(self.user).search(domain)

        self.assertIn(self.product_template1, products)
        self.assertNotIn(self.product_template2, products)

    def test_02_product_access_in_website(self):
        # Check that the user can access the product page of a product in their list
        self.authenticate('test_user', 'test_user')
        response = self.url_open('/shop/product/%s' % self.product_template1.id)
        self.assertEqual(response.status_code, 200)  # should respond with status 200 OK
        
        # Check that the user can't access the product page of a product not in their list
        with self.assertRaises(exceptions.AccessError), self.cr.savepoint():
            # The product page should raise a NotFound error, 
            # which in turn should cause an AccessError due to the lack of read access
            self.url_open('/shop/product/%s' % self.product_template2.id)
