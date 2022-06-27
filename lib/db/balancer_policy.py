from typing import Optional
from abc import abstractmethod
import random


class BalancerPolicy:
    """
        Implements greedy balancer policy for pool manager
        Returns less loaded pool
    """
    def __init__(self, pool_manager):
        self._pool_manager = pool_manager

    async def get_pool(
            self,
            read_only: bool,
            fallback_master: Optional[bool] = None,
            master_as_replica_weight: Optional[float] = None
    ):
        if not read_only and master_as_replica_weight is not None:
            raise ValueError(
                "Field master_as_replica_weight is used only when "
                "read_only is True",
            )

        choose_master_as_replica = False
        if master_as_replica_weight is not None:
            rand = random.random()
            choose_master_as_replica = 0 < rand <= master_as_replica_weight

        return await self._get_pool(
            read_only=read_only,
            fallback_master=fallback_master or choose_master_as_replica,
            choose_master_as_replica=choose_master_as_replica,
        )

    @abstractmethod
    async def _get_pool(
            self,
            read_only: bool,
            fallback_master: Optional[bool] = None,
            choose_master_as_replica: bool = False
    ):
        candidates = []
        if read_only:
            candidates.extend(
                await self._pool_manager.get_replica_pools(
                    fallback_master=fallback_master
                )
            )

        if (
            not read_only or
            (
                choose_master_as_replica and
                self._pool_manager.master_pool_count > 0
            )
        ):
            candidates.extend(await self._pool_manager.get_master_pools())

        fat_pool = max(candidates, key=self._pool_manager.get_pool_freesize)
        max_freesize = self._pool_manager.get_pool_freesize(fat_pool)

        return random.choice([
            candidate
            for candidate in candidates
            if self._pool_manager.get_pool_freesize(candidate) == max_freesize
        ])
