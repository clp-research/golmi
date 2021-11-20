class Mover:
    def __init__(self, model):
        self.model = model

    def _gripper_can_move(self, gr_id, dx, dy):
        """
        check if a gripper can be moved on the grid
        if the movement type is not move this function
        will always return True as dx and dy will be zero
        """
        gripper_x, gripper_y = self.get_gripper_coords(gr_id)
        new_gr_pos = {"x": gripper_x + dx, "y": gripper_y + dy}
        return new_gr_pos in self.object_grid

    def _get_new_coordinates(self, gr_obj, **kwargs):
        """
        based on the type of movement this function will
        return the new coordinates after the movement
        """
        d_angle = None

        if kwargs["type"] == "move":
            dx = kwargs["dx"]
            dy = kwargs["dy"]
            new_coordinates = gr_obj.occupied(
                gr_obj.x + dx, gr_obj.y + dy, gr_obj.block_matrix
            )
            new_matrix = gr_obj.block_matrix

        elif kwargs["type"] == "rotate":
            if "rotation_step" not in kwargs:
                step_size = self.model.config.rotation_step

            direction = kwargs["direction"]
            # determine the turning angle
            d_angle = direction * step_size

            # obtain rotated matrix
            new_matrix = self.state.rotate_block_matrix(
                gr_obj.block_matrix, d_angle
            )

            new_coordinates = gr_obj.occupied(
                gr_obj.x, gr_obj.y, new_matrix
            )

        elif kwargs["type"] == "flip":
            # obtain flipped matrix
            new_matrix = self.model.state.flip_block_matrix(
                gr_obj.block_matrix
            )

            new_coordinates = gr_obj.occupied(
                gr_obj.x, gr_obj.y, new_matrix
            )

        return new_coordinates, new_matrix, d_angle

    def apply_movement(self, movement_type, gr_id, **kwargs):
        """
        This class applies one of the movements
        """
        # gripper only moves if we have a move type movement
        dx = 0
        dy = 0
        if kwargs["type"] == "move":
            # if step size is not defined, use standard from config
            if "step_size" not in kwargs:
                step_size = self.model.config.move_step

            dx = kwargs["x_steps"] * step_size
            dy = kwargs["y_steps"] * step_size

        gripper_can_move = self._gripper_can_move(gr_id, dx, dy)

        if gripper_can_move:
            # check if gripper has an object
            gr_obj_id = self.get_gripped_obj(gr_id)
            if gr_obj_id:
                gr_obj = self.get_obj_by_id(gr_obj_id)

                # initialize empty variables for kwargs
                direction = None
                rotation_step = None
                
                if "direction" in kwargs:
                    direction = kwargs["direction"]

                if "rotation_step" in kwargs:
                    rotation_step = kwargs["rotation_step"]

                new_coordinates, new_matrix, d_angle = self._get_new_coordinates(
                    gr_obj,
                    type=movement_type,
                    dx=dx,
                    dy=dy,
                    direction=direction,
                    rotation_step=rotation_step
                )

                # check if coordinates are legal
                obj_can_move = self.object_grid.can_move(
                    new_coordinates, gr_obj_id
                )

                # apply movement
                if self.model.config.prevent_overlap and obj_can_move:
                    # remove object from grid
                    self.model.object_grid.remove_obj(gr_obj)

                    # apply movement according to type
                    if movement_type == "move":
                        self._move(gr_id, dx, dy)

                    elif movement_type == "flip":
                        self._flip(gr_obj_id, new_matrix)

                    elif movement_type == "rotate":
                        self._rotate(gr_obj_id, d_angle, new_matrix)

                    # add element to grid
                    self.object_grid.add_obj(gr_obj)

                    # if self.model.verbose is True:
                    #     print(self.model.object_grid)
                    print(self.model.object_grid)

            else:
                # only move the gripper
                self.state.move_gr(gr_id, dx, dy)

        # send update to views
        self._notify_views("update_grippers", self.get_gripper_dict())

    def _move(self, gr_id, dx, dy):
        """
        movement on grid
        """
        self.model.state.move_gr(gr_id, dx, dy)
        self.model.state.move_obj(self.model.get_gripped_obj(gr_id), dx, dy)

    def _rotate(self, gr_obj_id, d_angle, new_matrix):
        """
        rotation
        """
        # update state
        self.model.state.rotate_obj(gr_obj_id, d_angle, new_matrix)

    def _flip(self, gr_obj_id, new_matrix):
        """
        flip
        """
        # update state
        self.model.state.flip_obj(gr_obj_id, new_matrix)