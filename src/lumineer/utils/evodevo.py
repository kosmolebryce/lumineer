# `src/lumineer/utils/evodevo.py`
import numpy as np
import os
import pandas as pd
from pandas import DataFrame as df
from pathlib import Path
from typing import Optional

class Population:
    """
    Methods for quickly deriving populatin genetics insights
    """
    def __init__(
        self,
        data_dir: Path=Path("~/Notebooks/Evodevo").expanduser(),
        course_code: str="",
        **kwargs
    ) -> None:
        self.data_dir = data_dir
        self.course_code = course_code
        if not self.data_dir.exists():
            try:
                data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(e)
        else:
            print(f"Found {self.data_dir}")
            

    @staticmethod
    def msbalance(
        ploidy: str = "diploid",
        µ: Optional[float] = None,
        s: Optional[float] = None,
        q: Optional[float] = None
    ) -> float:
        """
        Calculate the mutation-selection balance for haploid or diploid organisms.
        
        Args:
        ploidy (str): Either 'haploid' or 'diploid'.
        µ (float, optional): Mutation rate.
        s (float, optional): Selection coefficient.
        q (float, optional): Equilibrium frequency of the deleterious allele.
        
        Returns:
        float: The calculated value for the missing parameter (µ, s, or q).
        
        Raises:
        ValueError: If ploidy is invalid or if not exactly two of µ, s, and q are provided.
        TypeError: If µ, s, or q are not float when provided.
        """
        if ploidy not in ["haploid", "diploid"]:
            raise ValueError(f"`ploidy` must be specified as either 'haploid' or 'diploid', not '{ploidy}'.")
        
        for param, name in [(µ, 'µ'), (s, 's'), (q, 'q')]:
            if param is not None:
                if not isinstance(param, float):
                    raise TypeError(f"`{name}` must be `float` or `None`.")
                if not 0 <= param <= 1:
                    raise ValueError(f"`{name}` must be between `0` and `1`.")
        
        if sum(x is not None for x in (µ, s, q)) != 2:
            raise ValueError("Exactly two of `µ`, `s`, and `q` must be provided.")
        
        is_haploid = ploidy == "haploid"
        
        if µ is not None and s is not None:
            return float(µ / s) if is_haploid else float(np.sqrt(µ / s))
        elif µ is not None and q is not None:
            return float(µ / q) if is_haploid else float(µ / (q ** 2))
        else:  # s is not None and q is not None
            return float(s * q) if is_haploid else float((q ** 2) * s)

    @staticmethod
    def hwe(
        p: Optional[float] = None,
        q: Optional[float] = None
    ) -> Optional[df]:
        """
        Calculate Hardy-Weinberg equilibrium genotype frequencies.

        Args:
        p (float, optional): Frequency of one allele.
        q (float, optional): Frequency of the other allele.

        Returns:
        df or None: DataFrame with genotype frequencies if calculation is successful, None otherwise.

        Raises:
        ValueError: If neither p nor q is provided, or if input values are invalid.
        """
        if p is None and q is None:
            raise ValueError("At least one of p or q must be provided.")
        
        if p is not None:
            if not 0 <= p <= 1:
                raise ValueError("p must be between 0 and 1.")
            q = 1 - p
        elif q is not None:
            if not 0 <= q <= 1:
                raise ValueError("q must be between 0 and 1.")
            p = 1 - q
        
        pp = p ** 2
        qq = q ** 2
        pq = 2 * p * q

        data = df([{
            "AA": pp,
            "aa": qq,
            "Aa": pq
        }])

        if abs(sum(data.iloc[0]) - 1) < 1e-10:  # Using a small tolerance for floating-point comparison
            return data
        else:
            raise ValueError(f"Error: Sum of genotype frequencies ({sum(data.iloc[0])}) does not equal 1.")
    