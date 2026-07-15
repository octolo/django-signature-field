(function () {
    "use strict";

    function debounce(fn, delay) {
        let timeoutId = null;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function preventScrollWhileDrawing(isDrawing) {
        return function (event) {
            if (isDrawing()) {
                event.preventDefault();
            }
        };
    }

    function escapeAttr(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function buildWidgetMarkup(config) {
        const labels = config.labels || {};
        const name = config.name || "signature";
        const promptLabel = config.initialMode
            ? (labels.initials || "Initials")
            : (labels.signatureText || "Signature text");
        const limit = config.maxChars
            ? `<div class="sw-limit" data-sw-limit><span class="sw-limit-value">${escapeAttr(config.maxChars)}</span></div>`
            : "";
        return `
<input type="hidden" name="${escapeAttr(name)}" data-signature-input>
<input type="hidden" name="${escapeAttr(name)}__drawn" value="0" data-signature-drawn>
<div class="sw-signature" data-sw-signature>
    <div class="sw-actions">
        <div class="sw-font-picker" data-sw-font-picker>
            <button type="button" class="sw-font-prev" data-sw-font-prev aria-label="${escapeAttr(labels.previousFont || "Previous font")}">\u25C0</button>
            <span class="sw-font-label" data-sw-font-label></span>
            <button type="button" class="sw-font-next" data-sw-font-next aria-label="${escapeAttr(labels.nextFont || "Next font")}">\u25B6</button>
        </div>
        <div class="sw-actions-right">
            <button type="button" class="sw-text-edit" data-sw-text-edit data-prompt-label="${escapeAttr(promptLabel)}" aria-label="${escapeAttr(labels.editText || "Edit text")}">\u2328</button>
            <button type="button" class="sw-clear" data-sw-clear hidden data-clear-label="${escapeAttr(labels.clear || "Clear")}" data-remove-label="${escapeAttr(labels.remove || "Remove signature")}" aria-label="${escapeAttr(labels.clear || "Clear")}">\u00D7</button>
        </div>
    </div>
    <canvas data-sw-canvas></canvas>
    ${limit}
</div>`;
    }

    class SignaturePad {
        constructor(root) {
            this.root = root;
            this.config = JSON.parse(root.dataset.config || "{}");

            if (!root.querySelector("[data-sw-canvas]")) {
                root.innerHTML = buildWidgetMarkup(this.config);
            }

            this.input = root.querySelector("[data-signature-input]");
            this.drawnInput = root.querySelector("[data-signature-drawn]");
            this.canvas = root.querySelector("[data-sw-canvas]");
            this.fontPicker = root.querySelector("[data-sw-font-picker]");
            this.fontLabel = root.querySelector("[data-sw-font-label]");
            this.fontPrevBtn = root.querySelector("[data-sw-font-prev]");
            this.fontNextBtn = root.querySelector("[data-sw-font-next]");
            this.textEditBtn = root.querySelector("[data-sw-text-edit]");
            this.clearBtn = root.querySelector("[data-sw-clear]");
            this.limitIndicator = root.querySelector("[data-sw-limit]");
            this.signatureBox = root.querySelector("[data-sw-signature]");

            if (!this.input.value && this.config.value) {
                this.input.value = this.config.value;
            }

            this.fonts = this.config.fonts || [];
            this.fontIndex = 0;
            this.textValue = this.config.text || this.config.signerName || "";
            this.initial = this.input.value || null;
            this.current = this.initial;
            this.userRedrawn = false;
            this.ready = false;
            this.documentDrawingBound = false;
            this.isDrawing = false;
            this.lastX = null;
            this.lastY = null;
            this.prevX = null;
            this.prevY = null;

            this.textCanvas = document.createElement("canvas");
            this.strokeCanvas = document.createElement("canvas");
            this.context = this.canvas.getContext("2d");
            this.textContext = this.textCanvas.getContext("2d");
            this.strokeContext = this.strokeCanvas.getContext("2d");

            this.onTouchStart = preventScrollWhileDrawing(() => this.isDrawing);
            this.onTouchMove = this.onTouchStart;
            this.debouncedRenderTypedText = debounce(() => {
                if (this.isReadOnly()) {
                    return;
                }
                this.renderTypedTextFromUser();
            }, 300);

            this.initFonts();
            this.bindEvents();
            this.initCanvas();
            if (!this.config.canvasWidth) {
                this.resizeObserver = new ResizeObserver(() => this.handleResize());
                this.resizeObserver.observe(this.root);
            }
            this.ready = true;
            this.updateUi();
        }

        initFonts() {
            if (!this.fonts.length) {
                if (this.fontPicker) {
                    this.fontPicker.hidden = true;
                }
                return;
            }
            const defaultFont = this.config.defaultFont || this.fonts[0].id;
            const defaultIndex = this.fonts.findIndex((font) => font.id === defaultFont);
            this.fontIndex = defaultIndex >= 0 ? defaultIndex : 0;
            this.updateFontDisplay();
        }

        updateFontDisplay() {
            if (!this.fontLabel || !this.fonts.length) {
                return;
            }
            const font = this.fonts[this.fontIndex];
            const label = font ? font.label : "";
            this.fontLabel.textContent = label;
            this.fontLabel.title = label;
        }

        shiftFont(delta) {
            if (!this.fonts.length || this.isReadOnly()) {
                return;
            }
            this.fontIndex = (this.fontIndex + delta + this.fonts.length) % this.fonts.length;
            this.updateFontDisplay();
            this.debouncedRenderTypedText();
        }

        getSelectedFont() {
            return this.fonts[this.fontIndex] || this.fonts[0] || null;
        }

        bindEvents() {
            this.onDocumentMouseMove = (event) => {
                if (!this.isDrawing || !this.canDraw()) {
                    return;
                }
                const point = this.pointerPoint(event.clientX, event.clientY);
                if (point) {
                    this.drawAt(point.x, point.y);
                }
            };
            this.onDocumentMouseUp = () => this.stopDrawing();
            this.onDocumentTouchMove = (event) => {
                if (!this.isDrawing || !this.canDraw()) {
                    return;
                }
                event.preventDefault();
                const point = this.touchPoint(event);
                if (point) {
                    this.drawAt(point.x, point.y);
                }
            };
            this.onDocumentTouchEnd = () => this.stopDrawing();

            this.canvas.addEventListener("mousedown", (event) => {
                if (!this.canDraw()) {
                    return;
                }
                const point = this.pointerPoint(event.clientX, event.clientY);
                if (!point) {
                    return;
                }
                this.startDrawing(point.x, point.y);
                this.bindDocumentDrawing();
            });

            this.canvas.addEventListener("touchstart", (event) => {
                if (!this.canDraw()) {
                    return;
                }
                event.preventDefault();
                const point = this.touchPoint(event);
                if (!point) {
                    return;
                }
                this.startDrawing(point.x, point.y);
                this.bindDocumentDrawing();
            }, { passive: false });

            document.body.addEventListener("touchstart", this.onTouchStart, { passive: false });
            document.body.addEventListener("touchmove", this.onTouchMove, { passive: false });

            this.fontPrevBtn.addEventListener("click", () => this.shiftFont(-1));
            this.fontNextBtn.addEventListener("click", () => this.shiftFont(1));
            this.textEditBtn.addEventListener("click", () => this.editTextViaPrompt());

            this.clearBtn.addEventListener("click", () => {
                if (this.canRemove()) {
                    this.removeSignature();
                } else {
                    this.clearCanvas();
                }
            });
        }

        destroy() {
            this.unbindDocumentDrawing();
            document.body.removeEventListener("touchstart", this.onTouchStart);
            document.body.removeEventListener("touchmove", this.onTouchMove);
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
            }
        }

        canDraw() {
            return !this.isReadOnly();
        }

        isReadOnly() {
            if (this.config.lockAsSigned && this.initial) {
                return true;
            }
            if (!this.config.allowRedraw && this.initial) {
                return true;
            }
            return false;
        }

        canRemove() {
            return this.config.manage && Boolean(this.initial);
        }

        isLocked() {
            return this.isReadOnly();
        }

        hasStoredSignature() {
            return Boolean(this.initial);
        }

        initCanvas() {
            const width = this.config.canvasWidth || Math.max(
                this.root.getBoundingClientRect().width - 10,
                this.config.canvasMinWidth || 500
            );
            const height = this.config.canvasHeight || Math.max(
                this.config.canvasMinHeight || 200,
                200
            );

            this.setCanvasSize(width, height);

            if (this.config.canvasWidth && this.config.canvasHeight) {
                this.root.classList.add("has-fixed-size");
            }

            this.textValue = this.config.text || this.config.signerName || "";
            if (this.config.initialMode) {
                this.textValue = this.normalizeTextValue(this.textValue);
            }

            if (this.initial) {
                this.loadImage(this.initial);
            } else if (this.textValue) {
                this.renderTypedText();
            }
        }

        normalizeTextValue(value) {
            if (!this.config.initialMode) {
                return (value || "").trim();
            }
            const maxChars = this.config.maxChars || 3;
            return (value || "")
                .replace(/\s+/g, "")
                .slice(0, maxChars)
                .toUpperCase();
        }

        getTypedText() {
            return this.normalizeTextValue(this.textValue);
        }

        getDefaultTextValue() {
            return this.normalizeTextValue(this.config.text || this.config.signerName || "");
        }

        editTextViaPrompt() {
            if (this.isReadOnly()) {
                return;
            }
            const label = this.textEditBtn.dataset.promptLabel || "Text";
            const value = window.prompt(label, this.getTypedText());
            if (value === null) {
                return;
            }
            this.textValue = this.normalizeTextValue(value);
            this.renderTypedTextFromUser();
        }

        setCanvasSize(width, height) {
            this.canvas.width = width;
            this.canvas.height = height;
            this.textCanvas.width = width;
            this.textCanvas.height = height;
            this.strokeCanvas.width = width;
            this.strokeCanvas.height = height;
            this.applyDisplaySize(width, height);
            this.applyStrokeStyle(this.strokeContext);
        }

        applyDisplaySize(width, height) {
            if (!this.config.canvasWidth || !this.config.canvasHeight) {
                return;
            }
            this.signatureBox.style.width = `${width}px`;
            this.signatureBox.style.maxWidth = "";
            this.canvas.style.width = `${width}px`;
            this.canvas.style.height = `${height}px`;
        }

        refreshComposite() {
            this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.context.drawImage(this.textCanvas, 0, 0);
            this.context.drawImage(this.strokeCanvas, 0, 0);
            this.current = this.hasContent() ? this.canvas.toDataURL("image/png") : null;
            this.syncInput();
        }

        syncInput() {
            const value = this.current || "";
            if (this.input.value !== value) {
                this.input.value = value;
                this.input.dispatchEvent(new Event("change", { bubbles: true }));
            }
            if (this.drawnInput) {
                this.drawnInput.value = this.userRedrawn ? "1" : "0";
            }
        }

        markRedrawn() {
            if (this.isReadOnly()) {
                return;
            }
            this.userRedrawn = true;
            if (this.drawnInput) {
                this.drawnInput.value = "1";
            }
        }

        hasContent() {
            return this.hasVisibleContent();
        }

        hasVisibleContent() {
            return this.hasCanvasPixels(this.textCanvas) || this.hasCanvasPixels(this.strokeCanvas);
        }

        hasCanvasPixels(canvas) {
            if (!canvas.width || !canvas.height) {
                return false;
            }
            const context = canvas.getContext("2d");
            const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
            for (let i = 3; i < data.length; i += 4) {
                if (data[i] !== 0) {
                    return true;
                }
            }
            return false;
        }

        hasStrokes() {
            return this.hasCanvasPixels(this.strokeCanvas);
        }

        handleResize() {
            if (this.config.canvasWidth || this.isReadOnly()) {
                return;
            }
            const previous = this.current;
            const width = Math.max(
                this.root.getBoundingClientRect().width - 10,
                this.config.canvasMinWidth || 500
            );
            const height = Math.max(this.config.canvasMinHeight || 200, 200);
            this.setCanvasSize(width, height);
            if (this.getTypedText()) {
                this.renderTypedText();
            } else if (previous) {
                this.loadImage(previous);
            } else {
                this.refreshComposite();
            }
        }

        applyStrokeStyle(context) {
            context.strokeStyle = "black";
            context.lineWidth = this.config.lineWidth || 0.8;
            context.lineCap = "round";
            context.lineJoin = "round";
        }

        touchPoint(event) {
            const touch = event.touches[0] || event.changedTouches[0];
            if (!touch) {
                return null;
            }
            return this.pointerPoint(touch.clientX, touch.clientY);
        }

        pointerPoint(clientX, clientY) {
            const rect = this.canvas.getBoundingClientRect();
            if (!rect.width || !rect.height) {
                return null;
            }
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;
            return {
                x: (clientX - rect.left) * scaleX,
                y: (clientY - rect.top) * scaleY,
            };
        }

        bindDocumentDrawing() {
            if (this.documentDrawingBound) {
                return;
            }
            this.documentDrawingBound = true;
            document.addEventListener("mousemove", this.onDocumentMouseMove);
            document.addEventListener("mouseup", this.onDocumentMouseUp);
            document.addEventListener("touchmove", this.onDocumentTouchMove, { passive: false });
            document.addEventListener("touchend", this.onDocumentTouchEnd);
            document.addEventListener("touchcancel", this.onDocumentTouchEnd);
        }

        unbindDocumentDrawing() {
            if (!this.documentDrawingBound) {
                return;
            }
            document.removeEventListener("mousemove", this.onDocumentMouseMove);
            document.removeEventListener("mouseup", this.onDocumentMouseUp);
            document.removeEventListener("touchmove", this.onDocumentTouchMove);
            document.removeEventListener("touchend", this.onDocumentTouchEnd);
            document.removeEventListener("touchcancel", this.onDocumentTouchEnd);
            this.documentDrawingBound = false;
        }

        wrapText(text, maxWidth, context) {
            const words = text.split(/\s+/).filter(Boolean);
            if (!words.length) {
                return [];
            }
            const lines = [words[0]];
            for (let i = 1; i < words.length; i += 1) {
                const word = words[i];
                const candidate = `${lines[lines.length - 1]} ${word}`;
                if (context.measureText(candidate).width <= maxWidth) {
                    lines[lines.length - 1] = candidate;
                } else {
                    lines.push(word);
                }
            }
            return lines;
        }

        measureLines(lines, context, fontSize) {
            const lineHeight = fontSize * 1.2;
            const widest = lines.reduce(
                (max, line) => Math.max(max, context.measureText(line).width),
                0
            );
            return {
                width: widest,
                height: lines.length * lineHeight,
                lineHeight,
            };
        }

        async loadFont(font, fontSize) {
            const fontSpec = `${fontSize}px "${font.family}"`;
            if (document.fonts && document.fonts.load) {
                await document.fonts.load(fontSpec);
            }
            this.textContext.font = fontSpec;
            return fontSpec;
        }

        async fitTextLayout(text, font) {
            const padding = this.config.initialMode ? 10 : 16;
            const maxWidth = this.textCanvas.width - padding * 2;
            const maxHeight = this.textCanvas.height - padding * 2;
            const maxFontSize = Math.min(
                maxHeight,
                this.config.fontSize || maxHeight,
                this.config.initialMode ? maxWidth : Math.floor(maxWidth * 0.5)
            );
            let low = 8;
            let high = Math.max(8, maxFontSize);
            let best = { fontSize: 8, lines: [text], lineHeight: 10 };

            while (low <= high) {
                const fontSize = Math.floor((low + high) / 2);
                await this.loadFont(font, fontSize);
                const lines = this.config.initialMode
                    ? [text]
                    : this.wrapText(text, maxWidth, this.textContext);
                const measured = this.measureLines(lines, this.textContext, fontSize);

                if (measured.width <= maxWidth && measured.height <= maxHeight) {
                    best = {
                        fontSize,
                        lines,
                        lineHeight: measured.lineHeight,
                    };
                    low = fontSize + 1;
                } else {
                    high = fontSize - 1;
                }
            }

            if (!best.lines.length) {
                best.lines = [text];
            }
            return best;
        }

        loadImage(dataUrl) {
            const img = new Image();
            img.onload = () => {
                this.userRedrawn = false;
                this.textContext.clearRect(0, 0, this.textCanvas.width, this.textCanvas.height);
                this.strokeContext.clearRect(0, 0, this.strokeCanvas.width, this.strokeCanvas.height);
                this.strokeContext.drawImage(
                    img,
                    0,
                    0,
                    this.strokeCanvas.width,
                    this.strokeCanvas.height
                );
                this.refreshComposite();
                this.updateUi();
            };
            img.src = dataUrl;
        }

        async renderTypedText() {
            if (this.isReadOnly()) {
                return;
            }
            const text = this.getTypedText();
            const font = this.getSelectedFont();

            this.textContext.clearRect(0, 0, this.textCanvas.width, this.textCanvas.height);

            if (text && font) {
                const layout = await this.fitTextLayout(text, font);
                await this.loadFont(font, layout.fontSize);

                this.textContext.fillStyle = "black";
                this.textContext.textAlign = "center";
                this.textContext.textBaseline = "middle";

                const startY = (this.textCanvas.height - layout.lines.length * layout.lineHeight) / 2;

                layout.lines.forEach((line, index) => {
                    this.textContext.fillText(
                        line,
                        this.textCanvas.width / 2,
                        startY + index * layout.lineHeight + layout.lineHeight / 2
                    );
                });
            }

            this.refreshComposite();
            this.updateUi();
        }

        async renderTypedTextFromUser() {
            this.markRedrawn();
            await this.renderTypedText();
        }

        startDrawing(x, y) {
            if (!this.canDraw()) {
                return;
            }
            this.isDrawing = true;
            this.signatureBox.classList.add("is-drawing");
            this.lastX = x;
            this.lastY = y;
            this.prevX = x;
            this.prevY = y;
        }

        drawAt(x, y) {
            if (!this.isDrawing || !this.canDraw()) {
                return;
            }
            this.markRedrawn();
            this.strokeContext.beginPath();
            this.strokeContext.moveTo(this.prevX, this.prevY);
            this.strokeContext.quadraticCurveTo(this.lastX, this.lastY, x, y);
            this.strokeContext.stroke();

            this.refreshComposite();

            this.prevX = this.lastX;
            this.prevY = this.lastY;
            this.lastX = x;
            this.lastY = y;
            this.updateUi();
        }

        stopDrawing() {
            if (!this.isDrawing) {
                return;
            }
            this.unbindDocumentDrawing();
            this.isDrawing = false;
            this.signatureBox.classList.remove("is-drawing");
            this.refreshComposite();
            this.updateUi();
        }

        clearCanvas(updateUi = true) {
            this.markRedrawn();
            this.textContext.clearRect(0, 0, this.textCanvas.width, this.textCanvas.height);
            this.strokeContext.clearRect(0, 0, this.strokeCanvas.width, this.strokeCanvas.height);
            this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.current = null;
            this.syncInput();
            if (updateUi) {
                this.updateUi();
            }
        }

        removeSignature() {
            this.markRedrawn();
            this.initial = null;
            this.current = null;
            this.syncInput();
            this.clearCanvas(false);
            this.textValue = this.getDefaultTextValue();
            if (this.textValue) {
                this.renderTypedText();
            } else {
                this.updateUi();
            }
        }

        updateUi() {
            const readOnly = this.isReadOnly();
            const hasContent = this.hasVisibleContent();
            const canRemove = this.canRemove();
            const showClear = (!readOnly && hasContent) || canRemove;

            this.root.classList.toggle("is-read-only", readOnly);
            this.signatureBox.classList.toggle("is-locked", readOnly && !this.config.manage);
            this.applyDisplaySize(this.canvas.width, this.canvas.height);
            this.clearBtn.hidden = !showClear;
            this.clearBtn.setAttribute(
                "aria-label",
                canRemove
                    ? (this.clearBtn.dataset.removeLabel || "Remove signature")
                    : (this.clearBtn.dataset.clearLabel || "Clear")
            );
            this.textEditBtn.hidden = readOnly;
            this.fontPrevBtn.disabled = readOnly || !this.fonts.length;
            this.fontNextBtn.disabled = readOnly || !this.fonts.length;
            if (this.fontPicker) {
                this.fontPicker.hidden = !this.fonts.length || readOnly;
            }
            if (this.limitIndicator) {
                this.limitIndicator.hidden = readOnly;
            }
        }
    }

    function initSignatureWidgets() {
        document.querySelectorAll("[data-signature-widget]").forEach((root) => {
            if (root.signaturePad) {
                return;
            }
            root.signaturePad = new SignaturePad(root);
        });
    }

    function createSignatureField(container, config) {
        const root = document.createElement("div");
        const settings = config || {};
        root.className = "signature-widget" + (settings.initialMode ? " is-initial-mode" : "");
        root.setAttribute("data-signature-widget", "");
        root.dataset.config = JSON.stringify(settings);
        container.appendChild(root);
        root.signaturePad = new SignaturePad(root);
        return root.signaturePad;
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSignatureWidgets);
    } else {
        initSignatureWidgets();
    }

    window.initSignatureWidgets = initSignatureWidgets;
    window.SignatureField = {
        SignaturePad,
        create: createSignatureField,
        init: initSignatureWidgets,
        buildMarkup: buildWidgetMarkup,
    };
})();
