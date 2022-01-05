$(document).ready(function () {

    this.SceneConfigControls = class SceneConfigControls {
        constructor(scene_config) {
            // Unique Properties Configuration
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
                // TODO: If variety is set for this prop
                // then set it to 2, if it is 1
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
                    min: 1, max: 7, // max minus 1 b.c. target piece
                    start: 7, step: 1,
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

            // Varieties Configuration
            $("#select_ambiguous_num_colors")
                .slider({
                    min: 1, max: 4,
                    start: 1, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_ambiguous_num_colors: " + value)
                        scene_config.ambiguity.num_colors = value
                    }
                })
            $("#select_ambiguous_num_shapes")
                .slider({
                    min: 1, max: 4,
                    start: 1, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_ambiguous_num_shapes: " + value)
                        scene_config.ambiguity.num_shapes = value
                    }
                })
            $("#select_ambiguous_num_positions")
                .slider({
                    min: 1, max: 4,
                    start: 1, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_ambiguous_num_positions: " + value)
                        scene_config.ambiguity.num_positions = value
                    }
                })
        }
    };
});