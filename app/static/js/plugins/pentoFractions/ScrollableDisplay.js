$(document).ready(function () {
    /**
     * Controls a scrollable text area.
     * @param {id of the text area DOM element} displayId
     */
    this.ScrollableDisplay = class ScrollableDisplay {
        constructor(displayId) {
            this.messages = document.getElementById(displayId);
            this.scrollToBottom();
        }

        /**
         * Display a new message at the end.
         */
        _addToEnd(message) {
            let newMessage = document.createElement("div");
            newMessage.innerHTML = message;
            this.messages.append(newMessage);
        }

        /**
         * Display a new message at the end.
         * @param {text to display} message
         */
        addMessage(message) {
            // Check if the display should scroll down to the bottom.
            let shouldScroll = this.messages.scrollTop + 
                this.messages.clientHeight === this.messages.scrollHeight;
            this._addToEnd(message);
            // Scroll down, if appropriate
            if (!shouldScroll) {
                this.scrollToBottom();
            }
        }

        scrollToBottom() {
            this.messages.scrollTop = this.messages.scrollHeight;
        }

    }; // class ScrollableDisplay end
}); // on document ready end

