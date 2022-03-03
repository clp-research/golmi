$(document).ready(function () {

    this.SceneConfigControls = class SceneConfigControls {
        constructor(scene_config) {
            // Unique Properties Configuration
            $("#select_target_color").dropdown({
                values: [
                    {name: "random", value: "RANDOM"},
                    {name: "red", value: "RED"},
                    {name: "orange", value: "ORANGE"},
                    {name: "yellow", value: "YELLOW"},
                    {name: "green", value: "GREEN"},
                    {name: "blue", value: "BLUE"},
                    {name: "purple", value: "PURPLE"},
                    {name: "brown", value: "BROWN"},
                    {name: "grey", value: "GREY"},
                    {name: "cyan", value: "CYAN"},
                    {name: "pink", value: "PINK"},
                    {name: "olive green", value: "OLIVE_GREEN"},
                    {name: "navy blue", value: "NAVY_BLUE"}
                ],
                onChange: function (value, text, $selectedItem) {
                    console.log("select_target_color: " + value)
                    scene_config.target_piece.color = value
                }
            })
            $("#select_target_shape").dropdown({
                values: [
                    {name: "random", value: "RANDOM"},
                    {name: "F", value: "F"},
                    {name: "I", value: "I"},
                    {name: "L", value: "L"},
                    {name: "N", value: "N"},
                    {name: "T", value: "T"},
                    {name: "U", value: "U"},
                    {name: "V", value: "V"},
                    {name: "W", value: "W"},
                    {name: "X", value: "X"},
                    {name: "Y", value: "Y"},
                    {name: "Z", value: "Z"}
                ],
                onChange: function (value, text, $selectedItem) {
                    console.log("select_target_shape: " + value)
                    scene_config.target_piece.shape = value
                }
            })
            $("#select_target_rel_position").dropdown({
                values: [
                    {name: "random", value: "RANDOM"},
                    {value: "TOP_LEFT", name: "top left"},
                    {value: "TOP_CENTER", name: "top center"},
                    {value: "TOP_RIGHT", name: "top right"},
                    {value: "CENTER_RIGHT", name: "right"},
                    {value: "BOTTOM_RIGHT", name: "bottom right"},
                    {value: "BOTTOM_CENTER", name: "bottom center"},
                    {value: "BOTTOM_LEFT", name: "bottom left"},
                    {value: "CENTER_LEFT", name: "left"},
                    {value: "CENTER", name: "center"}
                ],
                onChange: function (value, text, $selectedItem) {
                    console.log("select_target_rel_position: " + value)
                    scene_config.target_piece.rel_position = value
                }
            })
            $("#select_property").dropdown({
                onChange: function (value, text, $selectedItem) {
                    console.log("select_property: " + value)
                    scene_config.target_piece.unique_properties = [value]

                    $(".ambiguity").removeClass("disabled")

                    if (value === "color") {
                        $("#select_ambiguous_num_colors").addClass("disabled")
                    }
                    if (value === "shape") {
                        $("#select_ambiguous_num_shapes").addClass("disabled")
                    }
                    if (value === "rel_position") {
                        $("#select_ambiguous_num_positions").addClass("disabled")
                    }
                }
            })
            // Piece Configuration
            $("#select_num_distractors")
                .slider({
                    min: 1, max: 9,
                    start: 4, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_num_distractors: " + value)
                        scene_config.distractors.num_distractors = value
                    }
                })

            // Varieties Configuration
            $("#toggle_rotations").checkbox({
                value: true,
                onChecked: function () {
                },
                onUnchecked: function () {
                }
            })
            $("#select_variety_num_colors")
                .slider({
                    min: 1, max: 11, // max minus 1 b.c. target piece
                    start: 11, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_variety_num_colors: " + value)
                        scene_config.varieties.num_colors = value
                    },/*
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }*/
                })
            $("#select_variety_num_shapes")
                .slider({
                    min: 1, max: 11, // max minus 1 b.c. target piece
                    start: 11, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_variety_num_shapes: " + value)
                        scene_config.varieties.num_shapes = value
                    },/*
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }*/
                })
            $("#select_variety_num_positions")
                .slider({
                    min: 1, max: 8, // max minus 1 b.c. target piece
                    start: 8, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_variety_num_positions: " + value)
                        scene_config.varieties.num_positions = value
                    },/*
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value + 1;
                    }*/
                })
        }
    };
});