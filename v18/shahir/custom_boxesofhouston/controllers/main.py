# -*- coding: utf-8 -*-

from odoo.http import request, route
from odoo.tools import lazy
from odoo.osv import expression
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute
from odoo.addons.portal.controllers.portal import pager
from . import date_util as du
from datetime import date ,datetime, timedelta

from werkzeug.exceptions import NotFound 
from odoo import fields 
from odoo.tools import float_round, groupby, SQL
from odoo.tools.translate import _
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class WebsiteSaleCustom(WebsiteSale):
    def hide_out_of_stock(self, product):
        website = request.env['website'].get_current_website()
        total_free_qty = sum(website._get_product_available_qty(prod) for prod in product.sudo().product_variant_ids)
        if total_free_qty < 1:
            return False
        return product.id

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        fuzzy_search_term, product_count, search_result = super()._shop_lookup_products(attrib_set, options, post, search, website)
        product_count, details, fuzzy_search_term = website.sudo()._search_with_fuzzy("products_only", search,
                                                                               limit=None,
                                                                               order=self._get_search_order(post),
                                                                               options=options) 
        only_stock = request.session.get("stock", False)
        if only_stock:
            search_result = search_result.filtered(lambda product: self.hide_out_of_stock(product)) 
        return fuzzy_search_term, product_count, search_result
    
    @route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        if not category:
            request.session["stock"] = False
            return super(WebsiteSaleCustom, self).shop(page, category, search, min_price,max_price,ppg, **post)
        if not request.website.has_ecommerce_access():
            return request.redirect('/web/login')
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 0

        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()
        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = website.shop_ppg or 20

        ppr = website.shop_ppr or 4

        gap = website.shop_gap or "16px"

        # Custom added : Stock Only
        if category:
            only_stock = request.session.get("stock", False)
            if post.get("stock", False) == 'active':
                only_stock = True
            elif post.get("stock", False) == 'inactive':
                only_stock = False
            request.session["stock"] = only_stock 
        # ==============
        request_args = request.httprequest.args
        attrib_list = request_args.getlist('attribute_value')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        if attrib_list:
            post['attribute_value'] = attrib_list

        filter_by_tags_enabled = website.is_view_active('website_sale.filter_products_tags')
        if filter_by_tags_enabled:
            tags = request_args.getlist('tags')
            # Allow only numeric tag values to avoid internal error.
            if tags and all(tag.isnumeric() for tag in tags):
                post['tags'] = tags
                tags = {int(tag) for tag in tags}
            else:
                post['tags'] = None
                tags = {}

        keep = QueryURL('/shop', **self._shop_get_query_url_kwargs(category and int(category), search, min_price, max_price, **post))

        now = datetime.timestamp(datetime.now())
        pricelist = website.pricelist_id
        if 'website_sale_pricelist_time' in request.session:
            # Check if we need to refresh the cached pricelist
            pricelist_save_time = request.session['website_sale_pricelist_time']
            if pricelist_save_time < now - 60*60:
                request.session.pop('website_sale_current_pl', None)
                website.invalidate_recordset(['pricelist_id'])
                pricelist = website.pricelist_id
                request.session['website_sale_pricelist_time'] = now
                request.session['website_sale_current_pl'] = pricelist.id
        else:
            request.session['website_sale_pricelist_time'] = now
            request.session['website_sale_current_pl'] = pricelist.id

        filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            company_currency = website.company_id.sudo().currency_id
            conversion_rate = request.env['res.currency']._get_conversion_rate(
                company_currency, website.currency_id, request.website.company_id, fields.Date.today())
        else:
            conversion_rate = 1

        url = '/shop'
        if search:
            post['search'] = search

        options = self._get_search_options(
            category=category,
            attrib_values=attrib_values,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            display_currency=website.currency_id,
            **post
        )
        fuzzy_search_term, product_count, search_product = self._shop_lookup_products(attrib_set, options, post, search, website)

        filter_by_price_enabled = website.is_view_active('website_sale.filter_products_price')
        if filter_by_price_enabled:
            # TODO Find an alternative way to obtain the domain through the search metadata.
            Product = request.env['product.template'].with_context(bin_size=True)
            domain = self._get_shop_domain(search, category, attrib_values)

            # This is ~4 times more efficient than a search for the cheapest and most expensive products
            query = Product._where_calc(domain)
            Product._apply_ir_rules(query, 'read')
            sql = query.select(
                SQL(
                    "COALESCE(MIN(list_price), 0) * %(conversion_rate)s, COALESCE(MAX(list_price), 0) * %(conversion_rate)s",
                    conversion_rate=conversion_rate,
                )
            )
            available_min_price, available_max_price = request.env.execute_query(sql)[0]

            if min_price or max_price:
                # The if/else condition in the min_price / max_price value assignment
                # tackles the case where we switch to a list of products with different
                # available min / max prices than the ones set in the previous page.
                # In order to have logical results and not yield empty product lists, the
                # price filter is set to their respective available prices when the specified
                # min exceeds the max, and / or the specified max is lower than the available min.
                if min_price:
                    min_price = min_price if min_price <= available_max_price else available_min_price
                    post['min_price'] = min_price
                if max_price:
                    max_price = max_price if max_price >= available_min_price else available_max_price
                    post['max_price'] = max_price

        ProductTag = request.env['product.tag']
        if filter_by_tags_enabled and search_product:
            all_tags = ProductTag.search(
                expression.AND([
                    [('product_ids.is_published', '=', True), ('visible_on_ecommerce', '=', True)],
                    website_domain
                ])
            )
        else:
            all_tags = ProductTag

        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = lazy(lambda: Category.search(categs_domain))

        if category:
            url = "/shop/category/%s" % request.env['ir.http']._slug(category)

        pager = website.pager(url=url, total=product_count, page=page, step=ppg, scope=5, url_args=post)
        offset = pager['offset']
        products = search_product[offset:offset + ppg]

        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = lazy(lambda: ProductAttribute.search([
                ('product_tmpl_ids', 'in', search_product.ids),
                ('visibility', '=', 'visible'),
            ]))
        else:
            attributes = lazy(lambda: ProductAttribute.browse(attributes_ids))

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'
            request.session['website_sale_shop_layout_mode'] = layout_mode

        products_prices = lazy(lambda: products._get_sales_prices(website))

        attributes_values = request.env['product.attribute.value'].browse(attrib_set)
        sorted_attributes_values = attributes_values.sorted('sequence')
        multi_attributes_values = sorted_attributes_values.filtered(lambda av: av.display_type == 'multi')
        single_attributes_values = sorted_attributes_values - multi_attributes_values
        grouped_attributes_values = list(groupby(single_attributes_values, lambda av: av.attribute_id.id))
        grouped_attributes_values.extend([(av.attribute_id.id, [av]) for av in multi_attributes_values])

        selected_attributes_hash = grouped_attributes_values and "#attribute_values=%s" % (
            ','.join(str(v[0].id) for k, v in grouped_attributes_values)
        ) or ''
        # req quote task
        current_quote_ids = []
        current_quote = request.env['sale.order'].sudo().search([('state','=','draft'),('partner_id','=',request.env.user.partner_id.id),('custom_quote','=',True)],limit=1)
        if current_quote:
            current_quote_ids = current_quote.order_line.mapped('product_id.id')
        # --------------
        values = {
            'stock_only':request.session["stock"],
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'order': post.get('order', ''),
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'products': products,
            'search_product': search_product,
            'search_count': product_count,  # common for all searchbox
            'bins': lazy(lambda: TableCompute().process(products, ppg, ppr)),
            'ppg': ppg,
            'ppr': ppr,
            'gap': gap,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'selected_attributes_hash': selected_attributes_hash,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'products_prices': products_prices,
            'get_product_prices': lambda product: lazy(lambda: products_prices[product.id]),
            'float_round': float_round,
            'current_quote_ids':current_quote_ids or []
        }
        if filter_by_price_enabled:
            values['min_price'] = min_price or available_min_price
            values['max_price'] = max_price or available_max_price
            values['available_min_price'] = float_round(available_min_price, 2)
            values['available_max_price'] = float_round(available_max_price, 2)
        if filter_by_tags_enabled:
            values.update({'all_tags': all_tags, 'tags': tags})
        if category:
            values['main_object'] = category
        values.update(self._get_additional_extra_shop_values(values, **post))
        return request.render("custom_boxesofhouston.products_boxes", values)
    

    @route()
    def shop_address_submit(self, partner_id=None, address_type='billing', use_delivery_as_billing=None, callback=None,required_fields=None, **form_data):
        context = dict(request.context)
        context['ecommerce_create'] = True
        request.update_env(context=context)
        res = super().shop_address_submit(partner_id,address_type,use_delivery_as_billing,callback,required_fields,**form_data)
        return res
    
    @route(['/update/shop/cart'], type='json', auth="public", website=True, csrf=False)
    def update_cart_custom(self, product_id=False, qty=1, **kwargs): 
        try:
            if product_id:
                product_id = request.env['product.template'].sudo().browse(int(product_id))
                variant = product_id._get_first_possible_variant_id()
                order = request.website.sale_get_order(force_create=True)
                request.env['sale.order.line'].sudo().create({
                        'order_id': order.id,
                        'product_id': variant,
                        'product_uom_qty': int(qty), 
                    })
                request.session['website_sale_cart_quantity'] = order.cart_quantity
                return {
                    'cart_quantity':order.cart_quantity, 
                    'success':True,
                }
            else:
                return { 
                    'success':False,
                }

        except Exception as e:
            print(e)
        


    @route(['/create/quote'], type='json', auth="public", website=True, csrf=False)
    def create_quote(self, product_id=False, qty=1, **kwargs): 
        if not product_id:
            raise ValueError("Product ID is missing")
        qty = int(qty) if qty else 1 
        order = request.env['sale.order']
        partner = request.env.user.partner_id 
        order = order.sudo().search([('state','=','draft'),('partner_id','=',partner.id),('custom_quote','=',True)],limit=1)
        if not order:
            order_vals = {
                'partner_id': partner.id,
                'custom_quote': True,  
            } 
            order = order.sudo().create(order_vals)
        order_line = order.order_line.filtered(lambda a:a.product_id.id == int(product_id))
        if order_line:
            order_line.product_uom_qty = order_line.product_uom_qty+qty
        else:
            request.env['sale.order.line'].sudo().create({
                'order_id': order.id,
                'product_id': int(product_id),
                'product_uom_qty': qty, 
            })

        return {
            'success': True,
            'order_id': order.id,
            'message': "Custom Quote Created Successfully"
        }
    
    @route('/my/pricelist', type='http', auth="public", website=True,)
    def pricelist_list(self):
        quoted = []
        pending_quote = [] 
        vals = {
            'quoted':quoted,
            'pending_quote':pending_quote
        }
        return request.render('custom_boxesofhouston.custom_pricelist_list',vals)
        
    @route('/product/quoted', type='json', auth="user", website=True)
    def product_pricelist(self, qpage=1,ppage=1, page_size=10, qsearch="",psearch="",categs=[],stock="all"):
        product_obj = request.env['product.template'].sudo()
        website = request.env['website'].get_current_website() 
        quoted_ids = self.get_pending_quote_ids()
        pricelist_ids = product_obj.get_price_list_ids()
        q_domain= [('id', 'in', pricelist_ids)]
        pq_domain= []
        if qsearch:
            q_domain.append(('name', 'ilike', qsearch))
        if quoted_ids:
            pq_domain.append(('id', 'in', quoted_ids))
        if psearch:
            pq_domain.append(('name', 'ilike', psearch))
        if len(categs):
            categs = self.get_all_child_categs(categs)
            if categs:
                q_domain.append(('public_categ_ids', 'in', categs.ids))
                pq_domain.append(('public_categ_ids', 'in', categs.ids))
        # ------------
        quoted = []   
        quoted_products = product_obj.search(q_domain)
        quoted_products_prices = lazy(lambda: quoted_products._get_sales_prices(website))
        q_prices = lambda product: lazy(lambda: quoted_products_prices[product.id])
        if stock == 'in_stock':
            quoted_products = quoted_products.filtered(lambda a:a.qty_available)
        qpager = website.pager(url='/', total=len(quoted_products), page=qpage, step=8, scope=8, url_args={})
        offset = qpager['offset']
        quoted_products = quoted_products[offset:offset + 8] 
        for p in quoted_products:
            quoted.append({
                'id': p.id,
                'name': p.name,
                'url':p.website_url, 
                'price': self.get_product_price(p,q_prices(p)),
                'in_stock': self.get_stock_label(p),
                'available':True if p.qty_available else False
            })
        # ----------
        pquoted = [] 
        pending_products = request.env['product.template'].sudo().search(pq_domain)
        # pending_products_prices = lazy(lambda: pending_products._get_sales_prices(website))
        # p_prices = lambda product: lazy(lambda: pending_products_prices[product.id]) 
        if stock == 'in_stock':
            pending_products = pending_products.filtered(lambda a:a.qty_available)
        ppager = website.pager(url='/', total=len(pending_products), page=ppage, step=8, scope=8, url_args={})
        offset = ppager['offset']
        pending_products = pending_products[offset:offset + 8]
        
        for p in pending_products:
            pquoted.append({
                'id': p.id,
                'name': p.name,
                'url':p.website_url,
                'price': 0,
                'in_stock': self.get_stock_label(p),
                'available':True if p.qty_available else False
            })

        return { 
            'categories':self.get_all_parent_categs(),
            'quoted': quoted,
            'q_get_pager':qpager,
            'pending_quote':pquoted,  
            'p_get_pager':ppager, 
            'page_size': page_size,
            'currency':request.website.currency_id.symbol
        }
    
    def get_stock_label(self, product):
        if product.qty_available:
            return "In Stock"

        if not product.seller_ids:
            return "Not Available"

        delay = product.seller_ids[0].delay or 0
        if delay <= 0:
            return "Not Available"

        return f"{delay} Day{'s' if delay > 1 else ''}"
                
    def get_product_price(self,product,product_prices):
        website = request.website
        if product_prices['price_reduce'] or not website.prevent_zero_price_sale:
            return product_prices['price_reduce'] or 0
        else:
            return product_prices['base_price'] or 0  

    def get_pending_quote_ids(self):
        current_quote_ids = []
        current_quote = request.env['sale.order'].sudo().search([('state','=','draft'),('partner_id','=',request.env.user.partner_id.id),('custom_quote','=',True)],limit=1)
        if current_quote:
            current_quote_ids = current_quote.order_line.mapped('product_template_id.id')
        return current_quote_ids
    
    def get_all_parent_categs(self):
        categs = request.env['product.public.category'].sudo().search_read([('parent_id','=',False)],fields=['id','name'])
        return categs

    def get_all_child_categs(self,category_ids):
        return request.env['product.public.category'].search([('id', 'child_of', category_ids)])
 
    @route('/sales/data', type='json', auth="user", website=True)
    def dashboard_sales_data(self, params={}):
        product_obj = request.env['product.template'].sudo()
        website = request.env['website'].get_current_website() 
        new_leads = self.get_new_leads_per_salesperson(params.get('time_frame')) 

        return {
            'new_leads':new_leads['results'],
            'new_leads_count':new_leads['count']
        }
    
    def prepare_date_domain(self,date_field="create_date",time_frame='this_month'): 
        domain = [] 
        today = date.today()
        if time_frame: 
            if time_frame == "next_week":
                start_date, end_date = du.next_week_dates(today)
            elif time_frame == "next_month":
                start_date, end_date = du.next_month_dates(today) 
            elif time_frame == "this_week":
                start_date, end_date = du.current_week_dates(today)
            elif time_frame == "this_month":
                start_date, end_date = du.current_month_dates(today)
            elif time_frame == "this_year":
                start_date, end_date = du.current_year_dates(today) 
            elif time_frame == "last_week":
                start_date, end_date = du.past_week_dates(today)
            elif time_frame == "last_month":
                start_date, end_date = du.past_month_dates(today)  

            if start_date:
                if start_date == end_date:
                    end_date = start_date + timedelta(days=1)
                self.start_date = start_date
                domain.append((date_field,">=",fields.datetime.strftime(start_date, DEFAULT_SERVER_DATETIME_FORMAT),))

            if end_date:
                domain.append((date_field,"<",fields.datetime.strftime(end_date, DEFAULT_SERVER_DATETIME_FORMAT),))
        return domain
    
    def get_new_leads_per_salesperson(self,time_frame):
        date_domain = self.prepare_date_domain('create_date',time_frame) 
        leads_data = self.env['crm.lead'].read_group(date_domain,fields=['id'],
            groupby=['user_id'],
        ) 
        results = []
        total_leads = 0
        for rec in leads_data:
            total_leads += rec['id_count']
            results.append({
                'salesperson': rec.get('user_id')[1] if rec.get('user_id') else 'Unassigned',
                'new_leads_count': rec['id_count'],
            })
        return {
            'results':results,
            'count':total_leads,
        }