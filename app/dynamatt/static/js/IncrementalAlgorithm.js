$(document).ready(function () {

    // --- Incremental Algorithm by E. Reiter & R. Dale --- //

    /**
     * Func: IA
     * Construct a reference using the incremental algorithm.
     * Algorithm adapted from E. Reiter & R. Dale (1992).
     * See <https://aclanthology.org/C92-1038.pdf> and
     * the thesis for the full source and a description.
     */
    this.IA = class IA {
        constructor() {
            this.properties = ["color", "shape", "posRelBoard"];
            this.generalTypes = ["piece"];
            this.instrStart = ["Take", "Select", "Get"];
        }

        generate(currentObjects, currentTarget) {
            // preference order
            let P = this.properties;
            // construct a contrast set: first copy all objects into a set
            let C = new Set(Object.values(currentObjects));
            // target piece. Named r here to better match the pseudocode
            // by Reiter & Dale
            let r = currentTarget;
            // remove the target from the contrast set
            C.delete(r);

            // property-value pairs are collected here
            let L = [];

            for (let prop of P) {
                let val = this._findValue(r, prop);
                // check what objects would be eliminated using this prop-val pair
                let ruledOutObjs = this._rulesOut(prop, val, C);
                if (val && (ruledOutObjs.length > 0)) {
                    // save the property
                    L.push([prop, val]);
                    // update the contrast set
                    ruledOutObjs.forEach(ruledOut => C.delete(ruledOut));
                }

                // check if enough properties have been collected to rule out
                // all contrast objects
                if (C.size === 0) {
                    return document.randomFromArray(this.instrStart) + " the " + this._verbalizeRE(L);
                }
            }
            // no expression that rules out all contrast objects was found
            // original algorithm declares "IA: failure", but with the task at hand
            // this case is expected. User is supported by feedback.
            return document.randomFromArray(this.instrStart) + " the " + this._verbalizeRE(L);
        }

        /**
         * Helper function for IA.
         * Params:
         * prop - property name
         * val - value the target object has assigned to the given property
         * constrastSet - contrast set of objects to rule out by the given
         *        the property-value pair
         * Returns:
         * array of contrast objects with a different value for prop
         */
        _rulesOut(prop, val, contrastSet) {
            let ruledOutObjs = [];
            contrastSet.forEach(obj => {
                if (this._findValue(obj, prop) !== val) {
                    ruledOutObjs.push(obj);
                }
            });
            return ruledOutObjs;
        }


        /**
         * Determine the value an <Obj> has for a given property name.
         * Logs an error if the given property name is not implemented.
         * Params:
         * obj - IGView's representation of a GOLMI <Obj>
         * prop - _str_, property name
         * Returns: _str_, value matching _obj_
         */
        _findValue(obj, prop) {
            switch (prop) {
                case "shape":
                    return obj.type;
                case "color":
                    return obj.color;
                case "posRelBoard":
                    // describe top/bottom position
                    let val = "";
                    // the x / y properties of objects describe the upper left corner
                    // -> here we use the center coordinates instead
                    let x = obj.x + (obj.width / 2);
                    let y = obj.y + (obj.height / 2);
                    let fifth = this.width / 5;
                    if (y < 2 * fifth) {
                        val = "top";
                    } else if (y >= 3 * fifth) {
                        val = "bottom";
                    }
                    // describe left/right position
                    if (x < 2 * fifth) {
                        val = val.length > 0 ? val + " left" : "left";
                    } else if (x >= 3 * fifth) {
                        val = val.length > 0 ? val + " right" : "right";
                        // if no value was assigned yet, piece is in the center
                    } else if (val.length === 0) {
                        val = "center";
                    }
                    return val;
                default:
                    console.log(`Error at _findValue(): property ${prop} not implemented`);
                    return null;
            }
        }


        /**
         * Construct a natural language description from collected
         * property-value pairs.
         * Params:
         * propVals - object mapping property names to values
         * plural - _bool_, optional: pass true to produce a plural form
         * Returns: _str_, RE containing the values from _propVals_
         */
        _verbalizeRE(propVals, plural = false) {
            // property "id" is simply ignored
            let color = "", shape = "", posRelBoard = "";
            propVals.forEach(([prop, val]) => {
                switch (prop) {
                    case "color":
                        color = val;
                        break;
                    case "shape":
                        shape = val;
                        break;
                    case "posRelBoard":
                        posRelBoard = "in the " + val;
                        break;
                }
            });
            // if no shape given, use a generic noun
            shape = shape ? shape :
                this.generalTypes[Math.floor(Math.random() * this.generalTypes.length)];
            // special case: hpos and vpos are the only properties, but the gripper
            // is right above the piece so both have the value ""

            // add the values in a natural-sounding order
            return `${color} ${shape}${plural ? "s" : ""} ${posRelBoard}`;
        }
    }
});