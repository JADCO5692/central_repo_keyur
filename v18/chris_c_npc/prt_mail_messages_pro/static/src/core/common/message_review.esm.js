import {MessageReview} from "@prt_mail_messages/components/message_review.esm";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(MessageReview.prototype, {
    setup() {
        super.setup();
        this.Thread = useService("mail.store").Thread;
    },
    async openRecordReference(ev) {
        const recordRef = this.state.record.record_ref;
        const thread = await this.Thread.getOrFetch({
            model: recordRef.resModel,
            id: recordRef.resId,
        });
        if (thread) {
            thread.fetchAllMessages = true;
        }
        super.openRecordReference(ev);
    },
});
