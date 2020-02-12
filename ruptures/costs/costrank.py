r"""
.. _sec-costrank:

Centered rank signal
====================================================================================================

Description
----------------------------------------------------------------------------------------------------

This cost function detects changes in the mean rank of the segment
Formally, for a signal :math:`\{y_t\}_t` on an interval :math:`[a, b]`,

    .. math:: c_{rank}(a, b) = -(b - a) \bar{r_{a, b}}' \hat{\sigma_r^{-1}} \bar{r_{a, b}}

where :math:`\bar{r_{a, b}}` is the empirical mean of the sub-signal
:math:`\{r_t\}_{t=a+1}^b`, and :math:`\hat{sigma_r}` is the covariance matrix of the
overall rank signal :math:`r`.

Usage
----------------------------------------------------------------------------------------------------

Start with the usual imports and create a signal.

.. code-block:: python

    import numpy as np
    import matplotlib.pylab as plt
    import ruptures as rpt
    # creation of data
    n, dim = 500, 3  # number of samples, dimension
    n_bkps, sigma = 3, 5  # number of change points, noise standard deviation
    signal, bkps = rpt.pw_constant(n, dim, n_bkps, noise_std=sigma)

Then create a :class:`CostRank` instance and print the cost of the sub-signal :code:`signal[50:150]`.

.. code-block:: python

    c = rpt.costs.CostRank().fit(signal)
    print(c.error(50, 150))


You can also compute the sum of costs for a given list of change points.

.. code-block:: python

    print(c.sum_of_costs(bkps))
    print(c.sum_of_costs([10, 100, 200, 250, n]))


In order to use this cost class in a change point detection algorithm (inheriting from :class:`BaseEstimator`), either pass a :class:`CostRank` instance (through the argument ``'custom_cost'``) or set :code:`model="rank"`.

.. code-block:: python

    c = rpt.costs.CostRank(); algo = rpt.Dynp(custom_cost=c)
    # is equivalent to
    algo = rpt.Dynp(model="rank")


Code explanation
----------------------------------------------------------------------------------------------------

.. autoclass:: ruptures.costs.CostRank
    :members:
    :special-members: __init__

"""
import numpy as np
from numpy.linalg import inv

from ruptures.base import BaseCost
from ruptures.costs import NotEnoughPoints


class CostRank(BaseCost):
    r"""
    Centered rank signal
    """

    model = "rank"

    def __init__(self):
        self.cov = None
        self.ranks = None
        self.min_size = 2

    def fit(self, signal):
        """Set parameters of the instance.

        Args:
            signal (array): signal. Shape (n_samples,) or (n_samples, n_features)

        Returns:
            self
        """
        if signal.ndim == 1:
            signal = signal.reshape(-1, 1)

        # argsort gives us 0-based ranks
        ranks = np.argsort(signal, axis=0) + 1
        # normalise ranks into the range [0, 1)
        norm_ranks = ranks / len(signal)
        # Center the ranks into the range [-0.5, 0.5)
        centered_ranks = (norm_ranks - (1 / 2)).astype(int)
        # Sigma is the covariance of these ranks
        cov = np.cov(centered_ranks)

        self.cov = cov
        self.ranks = centered_ranks

        return self

    def error(self, start, end):
        """Return the approximation cost on the segment [start:end].

        Args:
            start (int): start of the segment
            end (int): end of the segment

        Returns:
            float: segment cost

        Raises:
            NotEnoughPoints: when the segment is too short (less than ``'min_size'`` samples).
        """
        if end - start < self.min_size:
            raise NotEnoughPoints

        mean = np.reshape(np.mean(self.ranks[start:end], axis=0), (-1, 1))

        # Possibly the inversion could be done more efficiently with the knowledge that
        # the cov matrix is positive semidefinite
        return -(end - start) * mean.T @ inv(self.cov) @ mean / len(self.ranks)
