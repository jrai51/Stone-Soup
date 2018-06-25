# -*- coding: utf-8 -*-
from functools import lru_cache

from .base import Updater
from ..base import Property
from ..resampler import Resampler
from ..types import Particle, ParticleState


class ParticleUpdater(Updater):
    """Simple Particle Updater

        Perform measurement update step in the standard Kalman Filter.
        """

    resampler = Property(Resampler,
                         doc='Resampler to prevent particle degeneracy')

    def update(self, prediction, measurement,
               measurement_prediction=None, **kwargs):
        """Particle Filter update step

        Parameters
        ----------
        prediction : :class:`ParticleState`
            The state prediction
        measurement : :class:`Detection`
            The measurement
        measurement_prediction : None
            Not required and ignored if passed.

        Returns
        -------
        : :class:`ParticleState`
            The state posterior
        """

        for particle in prediction.particles:
            particle.weight *= self.measurement_model.pdf(
                measurement.state_vector, particle.state_vector)

        # Normalise the weights
        sum_w = sum(i.weight for i in prediction.particles)
        if sum_w == 0:
            # Reset particles with equal weights
            new_particles = [
                Particle(
                    particle.state_vector,
                    weight=1 / len(prediction.particles),
                    parent=particle.parent)]
        else:
            # Normalise and resample
            for particle in prediction.particles:
                particle.weight /= sum_w
            new_particles = self.resampler.resample(prediction.particles)

        return ParticleState(new_particles, timestamp=prediction.timestamp)

    @lru_cache()
    def get_measurement_prediction(self, state_prediction):
        new_particles = []
        for particle in state_prediction.particles:
            new_state_vector = self.measurement_model.function(
                particle.state_vector, noise=0)
            new_particles.append(
                Particle(new_state_vector,
                         weight=particle.weight,
                         timestamp=state_prediction.timestamp,
                         parent=particle.parent))

        return ParticleState(
            new_particles, timestamp=state_prediction.timestamp)