# Scientific Methodology & Mathematical Formulations

## 1. Photometric Shading Model
Lunar surface reflectance is modeled using a hybrid Lunar-Lambertian / Lommel-Seeliger formulation:
$$I(i, e, \alpha) = \left[ (1 - c) \frac{\cos i}{\cos i + \cos e} + c \cos i \right] f(\alpha)$$
where:
- $i$: Incidence angle
- $e$: Emission angle
- $\alpha$: Phase angle
- $c \approx 0.65$: Lunar limb-darkening coefficient

## 2. Multi-Pillar Physics Evidence Scoring
The composite confidence $C_{\text{composite}}$ is calculated as:
$$C_{\text{composite}} = w_{\text{vis}} S_{\text{vis}} + w_{\text{geo}} S_{\text{geo}} + w_{\text{illum}} S_{\text{illum}} + w_{\text{terrain}} S_{\text{terrain}} + w_{\text{scale}} S_{\text{scale}} + w_{\text{spatial}} S_{\text{spatial}}$$
where:
- $w_{\text{geo}} = 0.30, w_{\text{vis}} = 0.20, w_{\text{illum}} = 0.20, w_{\text{terrain}} = 0.15, w_{\text{scale}} = 0.08, w_{\text{spatial}} = 0.07$

## 3. Spatial Entropy Formulations
To ensure keypoint correspondences are distributed across the full terrain frame rather than clumped on a single feature, spatial entropy is computed over a $4 \times 4$ spatial grid $B$:
$$H(S) = - \sum_{k=1}^{16} p_k \log_2(p_k)$$
where $p_k = \frac{n_k}{N}$ is the normalized match density in bin $k$.

## 4. Expected Information Gain Formulation
$$\mathbb{E}[\Delta I(\text{Entity}, \text{Sensor})] = U(\text{Entity}) \cdot R(\text{Sensor}, Q) \cdot M(\text{Entity}, \text{Sensor}) \cdot Q_{\text{sensor}} \cdot F_{\text{traj}}$$
This guides autonomous observation planning to maximize uncertainty reduction per orbit.
