import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";

patch(PartnerList.prototype, {
    async getNewPartners() {
        let domain = [];
        const limit = 30;
        if (this.state.query) {
            const search_fields = [
                "name",
                "parent_name",
                ...this.getPhoneSearchTerms(),
                "email",
                "barcode",
                "street",
                "zip",
                "city",
                "state_id",
                "country_id",
                "vat",
            ];
            domain = [
                ...Array(search_fields.length - 1).fill("|"),
                ...search_fields.map((field) => [field, "ilike", this.state.query + "%"]),
            ];
            const searchDomain = [
            ...Array(search_fields.length - 1).fill("|"),
            ...search_fields.map((field) => [field, "ilike", this.state.query + "%"]),
            ];
            
            // Combine with AND condition for parent_id = false
            domain = [
                "&",
                ["parent_id", "=", false],
                ...searchDomain
            ];
        } else {
            // If no query, just filter by parent_id = false
            domain = [["parent_id", "=", false]];
        }

        const result = await this.pos.data.searchRead("res.partner", domain, [], {
            limit: limit,
            offset: this.state.currentOffset,
        });

        return result;
    }
});
