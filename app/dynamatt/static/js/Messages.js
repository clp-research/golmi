$(document).ready(function () {
    this.Messages = class Messages {

        constructor() {
            this.msgQueue = []
        }

        /**
         * Prepare a message to deliver to the user. It will be played
         * once it reaches the top of the message queue.
         * Params:
         * msg - _str_, message to send
         * type - type of message, one of ["instruction", "feedback", "meta"],
         *        used for logging
         */
        queue(msg, type = "meta") {
            // get the audio filename: msg in lower case, without spaces or
            // special characters and with an .mp3 extension
            let msgFile = msg.toLowerCase();
            for (let char of [" ", ",", ".", "'", "!", "?"]) {
                msgFile = msgFile.replaceAll(char, "");
            }
            msgFile = "../matthew/static/resources/audio/" + msgFile + ".mp3";
            let audio = new Audio(msgFile);
            // Safari browser needs this line
            audio.load();
            // keep the message in the queue until it has been delivered, this way we have a
            // reference to it in case we need to abort playing
            this.msgQueue.push([msg, audio, type]);

            // if there is no other message currently playing, start this message immediately
            if (this.msgQueue.length === 1) {
                this._playNextMsg();
            }
        }

        /**
         * Func: abortAllMsgs
         * Stop any audio currently playing and delete waiting messages.
         */
        abortAllMsgs() {
            if (this._hasPendingMsg()) {
                this.msgQueue[0][1].pause();
                this.msgQueue.length = 0;
            }
        }

        /**
         * Play the first message waiting in the message queue.
         * Emits a 'emitMessage' event to the document.
         */
        _playNextMsg() {
            if (this._hasPendingMsg()) {
                // play the first message in the queue
                let [nextMsg, nextAudio, nextType] = this.msgQueue[0];
                // always display the text
                this._displayMsg();
                if (nextAudio.error) {
                    // dispatch message event (with error tag)
                    document.dispatchEvent(new CustomEvent("emitMessage", {
                        detail: {
                            "type": nextType, "content": nextMsg, "error": true
                        }
                    }));
                    // delete the message from the queue
                    this._msgEnded();
                    return;
                }
                nextAudio.onerror = () => this._displayMsg();
                nextAudio.onended = () => this._msgEnded();
                // dispatch event and play as soon as the audio is ready:
                if (nextAudio.readyState >= 2) {
                    document.dispatchEvent(new CustomEvent("emitMessage", {
                        detail: {
                            "type": nextType, "content": nextMsg, "duration": nextAudio.duration
                        }
                    }));
                    nextAudio.play();
                } else {
                    nextAudio.oncanplaythrough = function () {
                        // dispatch message event
                        document.dispatchEvent(new CustomEvent("emitMessage", {
                            detail: {
                                "type": nextType, "content": nextMsg, "duration": nextAudio.duration
                            }
                        }));
                        nextAudio.play();
                    };
                }
                this._msgEnded()
            }
        }

        /**
         * Fallback method for message delivery in case audio can't be used.
         * Not very user-friendly, prints to the interface.
         * Emits a 'emitMessage' event to the document.
         */
        _displayMsg() {
            if (this._hasPendingMsg()) {
                let [nextMsg, nextAudio, nextType] = this.msgQueue[0];
                // print message to console and display in the interface
                console.log(nextMsg);
                $("#instructions").text(nextMsg);
            }
        }

        /**
         * Delete any message currently displayed in the interface.
         * (see _displayNextMsg())
         */
        _emptyDisplay() {
            $("#instructions").text("");
        }

        /**
         * Function called after a message has been delivered (i.e. was
         * displayed or audio has ended). Reset gripper trace. Play the
         * next waiting message or restart the feedback timer.
         */
        _msgEnded() {
            // update the timestamp of the last message delivered to the user
            this.lastMsg = Date.now();
            // delete the audio from the queue
            let msgType = this.msgQueue[0][2];
            this.msgQueue = this.msgQueue.slice(1);
            // make sure any waiting message is played next
            if (this._hasPendingMsg()) {
                this._playNextMsg();
            }
        }

        /**
         * Check if the internal message queue contains pending messages.
         * Returns:
         * true if a message is currently playing or waiting to be played
         */
        _hasPendingMsg() {
            return this.msgQueue.length > 0;
        }
    }
});