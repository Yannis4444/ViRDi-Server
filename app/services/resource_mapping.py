import logging

from app.services.prosumer import Resource

logger = logging.getLogger(__name__)


class ResourceMapping:
    """
    A mapping from a game resource to a ViRDi resource.
    """

    @staticmethod
    def create_from_config(game_id: str, resource_id: str, config: dict) -> list['ResourceMapping']:
        """
        Create resource mappings from a config in the yaml files.

        :param game_id: The id for the game the mapping is for
        :param resource_id: The id of the ViRDi resource.
        :param config: The config from the yaml files
        :return: The Resource Mapping
        """

        mappings = []

        global_factor = config.get("factor", 1)
        global_divisor = config.get("divisor", 1)

        for c in config.get("game_ids", []):
            factor = global_factor
            divisor = global_divisor
            if isinstance(c, str):
                external_id = c
            else:
                external_id, inner_config = next(iter(c.items()))
                if inner_config is not None:
                    factor *= inner_config.get("factor", 1)
                    divisor *= inner_config.get("divisor", 1)

            resource = Resource.get(resource_id)

            if resource is None:
                raise ValueError(f"Found resource mapping without unknown resource id: {game_id=}, {resource_id=}, config={c}")

            if external_id is None:
                raise ValueError(f"Found resource mapping without external id: {game_id=}, {resource_id=}, config={c}")

            if not isinstance(factor, int) or not isinstance(divisor, int):
                raise ValueError(f"Resource Mapping {factor=} and {divisor=} have to be integers: {game_id=}, {resource_id=}, config={c}")

            logger.info(f"Creating Resource Mapping: {game_id}|{external_id} -> {resource_id} (factor={factor}, divisor={divisor})")

            mappings.append(ResourceMapping(resource, game_id, external_id, factor=factor, divisor=divisor))

        return mappings

    def __init__(self, resource: Resource, game_id: str, external_id: str, factor: int = 1, divisor: int = 1):
        """
        Creates a mapping for a resource in the given game to the given ViRDi resource.

        When a resource comes into the system,
        the external amount will be multiplied by the factor and divided by the divisor.
        The invers will happen when an item leaves the system.

        :param resource: The internally used resource
        :param game_id: The id for the game
        :param external_id: The ID for the resource as used by the game
        :param factor: A factor for the conversion between the external and ViRDi resource.
        :param divisor: A divisor for the conversion between the external and ViRDi resource.
        """

        self.resource = resource
        self.game_id = game_id
        self.external_id = external_id
        self.factor = factor
        self.divisor = divisor

        # TODO: use factor and divisor

    def __repr__(self):
        return f"ResourceMapping({self.game_id}|{self.external_id} -> {self.resource} (factor={self.factor}, divisor={self.divisor}))"

    def __str__(self):
        return f"ResourceMapping({self.game_id}|{self.external_id} -> {self.resource})"
