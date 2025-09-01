import {Thread} from "@mail/core/common/thread";
import {patch} from "@web/core/utils/patch";

patch(Thread.prototype, {
    async jumpToPresent() {
        super.jumpToPresent();
        await this.props.thread.setDefaultThreadFilters();
    },
});
