$(document).ready(function () {

    this.SceneConfigControls = class SceneConfigControls {
        constructor(scene_config) {
            // Unique Properties Configuration
            $("#select_property").dropdown({
                onChange: function (value, text, $selectedItem) {
                    console.log("select_property: " + value)
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
            $("#select_variety_num_colors")
                .slider({
                    min: 0, max: 8,
                    start: 0, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_variety_num_colors: " + value)
                        scene_config.varieties.num_colors = value
                    },
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }
                })
            $("#select_variety_num_shapes")
                .slider({
                    min: 0, max: 12,
                    start: 0, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_variety_num_shapes: " + value)
                        scene_config.varieties.num_shapes = value
                    },
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }
                })
            $("#select_variety_num_positions")
                .slider({
                    min: 0, max: 9,
                    start: 0, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_variety_num_positions: " + value)
                        scene_config.varieties.num_positions = value
                    },
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }
                })

            // Varieties Configuration
            $("#select_ambiguous_num_colors")
                .slider({
                    min: 0, max: 4,
                    start: 0, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_ambiguous_num_colors: " + value)
                        scene_config.ambiguity.num_colors = value
                    },
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }
                })
            $("#select_ambiguous_num_shapes")
                .slider({
                    min: 0, max: 4,
                    start: 0, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_ambiguous_num_shapes: " + value)
                        scene_config.ambiguity.num_shapes = value
                    },
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }
                })
            $("#select_ambiguous_num_positions")
                .slider({
                    min: 0, max: 4,
                    start: 1, step: 1,
                    onChange: function (value, text, $selectedItem) {
                        console.log("select_ambiguous_num_positions: " + value)
                        scene_config.ambiguity.num_positions = value
                    },
                    interpretLabel: function (value) {
                        return value === 0 ? "all" : value;
                    }
                })
        }
    };
});