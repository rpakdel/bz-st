from dataclasses import dataclass, field
from typing import List
import pandas as pd


@dataclass
class Block:
    """
    Simple container for a single block in the block model.

    Attributes:
        id: Unique integer identifier for the block.
        x, y, z: Integer coordinates (grid indices or real positions).
        attributes: List of numeric attributes for the block (e.g., tonnage, grade, value).
    """
    id: int
    x: int
    y: int
    z: int
    attributes: List[float]


@dataclass
class BlockModel:
    """
    Represents a collection of `Block` objects and optional attribute names.

    The class provides a convenience method `to_dataframe()` to convert the
    block list into a pandas DataFrame with columns: `id, x, y, z, <attributes...>`.

    Args:
        name: Human-readable name for the block model (instance name or dataset id).
        blocks: List of `Block` instances.
        attribute_names: Optional list of names for the numeric attributes in each block.
            If there are more numeric attributes than names, generated column names
            `attr_<i>` are appended to the DataFrame columns.
    """
    name: str
    blocks: List[Block]
    attribute_names: List[str] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the block model into a pandas DataFrame.

        Returns:
            pd.DataFrame: rows correspond to blocks; columns start with
            `id, x, y, z` followed by the named attributes (or generated names
            when `attribute_names` is shorter than the attribute vectors).

        Notes:
            - If the model has no blocks, an empty DataFrame with the appropriate
              columns is returned.
            - All blocks are expected to have the same number of numeric attributes.
        """
        data = []

        # Return an empty dataframe with the expected columns when there are no blocks
        if not self.blocks:
            columns = ["id", "x", "y", "z"] + self.attribute_names
            return pd.DataFrame(columns=columns)

        # Build row data for each block
        for b in self.blocks:
            row = [b.id, b.x, b.y, b.z] + b.attributes
            data.append(row)

        # Start with the standard columns, then append attribute names
        columns = ["id", "x", "y", "z"] + self.attribute_names

        # If blocks contain more attributes than we have names for, generate placeholder names
        num_attrs = len(self.blocks[0].attributes)
        if len(self.attribute_names) < num_attrs:
            for i in range(len(self.attribute_names), num_attrs):
                columns.append(f"attr_{i}")

        return pd.DataFrame(data, columns=columns)
