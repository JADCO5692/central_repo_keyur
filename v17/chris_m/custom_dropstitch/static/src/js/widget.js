/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class StockMoveProductsWidget extends Component {
    static template = "custom_dropstitch.StockMoveProductsWidget";
    static props = {
        ...standardFieldProps,
    };

    constructor() {
        super(...arguments);
        this.selectedOption = "";
    }


    setup() {
        this.orm = useService("orm");
        this.state = useState({ products: [], loading: true });
        onWillStart(async () => {
            await this.loadMoveProducts();
        });

    }

    get moveIds() {
        return this.props.record._values.move_ids_without_package._currentIds || [];
    }

    async loadMoveProducts() {
        if (!this.moveIds.length) return [];

        const moves = await this.orm.searchRead(
            "stock.move",
            [["id", "in", this.moveIds]],
            ["product_id"]
        );

        this.state.products = moves.map(move => ({
            id: move.id,
            product_id: move.product_id[0],
            product_name: move.product_id[1],
            product_image: `/web/image/product.product/${move.product_id[0]}/image_128`,
        }));
    }
}

export const StockMoveProductsWidgetComponent = {
    component: StockMoveProductsWidget,
    supportedTypes: ["text"],
};

registry.category("fields").add("stock_move_products", StockMoveProductsWidgetComponent);