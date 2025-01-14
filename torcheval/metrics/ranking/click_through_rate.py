# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

# pyre-ignore-all-errors[16]: Undefined attribute of metric states.

from typing import Iterable, Optional, TypeVar, Union

import torch

from torcheval.metrics.functional.ranking.click_through_rate import (
    _click_through_rate_compute,
    _click_through_rate_update,
)
from torcheval.metrics.metric import Metric


TClickThroughRate = TypeVar("TClickThroughRate")


class ClickThroughRate(Metric[torch.Tensor]):
    """
    Compute the click through rate given click events.
    Its functional version is ``torcheval.metrics.functional.click_through_rate``.

    Examples::

        >>> import torch
        >>> from torcheval.metrics.ranking import ClickThroughRate
        >>> metric = ClickThroughRate()
        >>> input = torch.tensor([0, 1, 0, 1, 1, 0, 0, 1])
        >>> metric.update(input)
        >>> metric.compute()
        tensor(0.5)
        >>> metric = ClickThroughRate()
        >>> weights = torch.tensor([1.0, 2.0, 1.0, 2.0, 1.0, 2.0, 1.0, 2.0])
        >>> metric.update(input, weights)
        >>> metric.compute()
        tensor(0.58333)
        >>> metric = ClickThroughRate()
        >>> input = torch.tensor([[0, 1, 0, 1], [1, 0, 0, 1]])
        >>> weights = torch.tensor([[1.0, 2.0, 1.0, 2.0],[1.0, 2.0, 1.0, 1.0]])
        >>> metric.update(input, weights)
        >>> metric.compute()
        tensor([0.6667, 0.4])

    """

    def __init__(
        self: TClickThroughRate,
        *,
        device: Optional[torch.device] = None,
    ) -> None:
        super().__init__(device=device)
        self._add_state("click_total", torch.tensor(0.0, device=self.device))
        self._add_state("weight_total", torch.tensor(0.0, device=self.device))

    @torch.inference_mode()
    # pyre-ignore[14]: `update` overrides method defined in `Metric` inconsistently.
    def update(
        self: TClickThroughRate,
        input: torch.Tensor,
        weights: Union[torch.Tensor, float, int] = 1.0,
    ) -> TClickThroughRate:
        """
        Update the metric state with new inputs.

        Args:
            input (Tensor): Series of values representing user click (1) or skip (0)
                            of shape (num_events) or (num_objectives, num_events).
            weights (Tensor, float, int): Weights for each event, single weight or tensor with the same shape as input.
        """
        click_total, weight_total = _click_through_rate_update(input, weights)
        self.click_total = self.click_total + click_total
        self.weight_total = self.weight_total + weight_total
        return self

    @torch.inference_mode()
    def compute(self: TClickThroughRate) -> torch.Tensor:
        """
        Return the stacked click through rank scores. If no ``update()`` calls are made before
        ``compute()`` is called, return tensor(0.0).
        """
        return _click_through_rate_compute(self.click_total, self.weight_total)

    @torch.inference_mode()
    def merge_state(
        self: TClickThroughRate, metrics: Iterable[TClickThroughRate]
    ) -> TClickThroughRate:
        """
        Merge the metric state with its counterparts from other metric instances.

        Args:
            metrics (Iterable[Metric]): metric instances whose states are to be merged.
        """
        for metric in metrics:
            self.click_total = self.click_total + metric.click_total.to(self.device)
            self.weight_total = self.weight_total + metric.weight_total.to(self.device)
        return self
