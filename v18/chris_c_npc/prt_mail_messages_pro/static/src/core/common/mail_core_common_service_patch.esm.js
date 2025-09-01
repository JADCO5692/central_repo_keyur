import {MailCoreCommon} from "@mail/core/common/mail_core_common_service";
import {patch} from "@web/core/utils/patch";

patch(MailCoreCommon.prototype, {
    setup() {
        super.setup();

        this.store.isReady.then(() => {
            this.busService.subscribe("mail.message/move", (payload) => {
                for (const message of payload.message_ids) {
                    const {id, data, originalThread, movedThread} = message;
                    let record = this.store.Message.get(id);
                    if (!record) {
                        record = this.store.Message.insert(data, {html: true});
                    }
                    if (originalThread) {
                        const oThread = this.store.Thread.get({
                            model: originalThread.thread_model,
                            id: originalThread.thread_id,
                        });
                        if (oThread) {
                            oThread.messages.delete(record);
                        }
                    }
                    if (movedThread) {
                        const mThread = this.store.Thread.get({
                            model: movedThread.thread_model,
                            id: movedThread.thread_id,
                        });
                        if (mThread) {
                            mThread.messages.add(record);
                        }
                    }
                    this.env.bus.trigger("reload-preview", {
                        threadId: movedThread.thread_id,
                        threadModel: movedThread.thread_model,
                        messageId: id,
                    });
                }
            });
            this.busService.subscribe("mail.message/edit", (payload) => {
                const {id, data} = payload;
                this.store.Message.insert(
                    {
                        id: id,
                        ...data,
                    },
                    {html: true}
                );
                this.env.bus.trigger("reload-preview");
            });
        });
    },
});
