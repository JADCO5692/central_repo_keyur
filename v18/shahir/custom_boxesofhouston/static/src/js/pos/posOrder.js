import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch"; 
import { _t } from "@web/core/l10n/translation"; 

patch(PosOrder.prototype, {
  setup(vals) {
    super.setup(...arguments);
    this.route_id = vals.route_id || false ;
  },
  setShippingRoute(route) {
    this.route_id = route;
  },
  serialize() {
      const data = super.serialize(...arguments); 
      if (this.route_id){
          data.route_id= this.route_id;
      } 
      return data;
    }
});