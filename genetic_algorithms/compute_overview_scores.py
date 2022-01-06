import numpy as np

results_meta = [
    {
        'name': 'Original Strombom',
        'res_path': 'results/evaluation.original_strombom.npy'
    },
    {
        'name': 'GA Strombom',
        'res_path': 'results/evaluation.ga_strombom.npy'
    },
    {
        'name': 'GA Sigmoid',
        'res_path': 'results/evaluation.sigmoid.transition_only.npy'
    },
        {
        'name': 'GA Sigmoid + Original Strombom',
        'res_path': 'results/evaluation.sigmoid.original_strombom.npy'
    }
]

analysis_range = 101

base = np.zeros((140, 140), dtype=bool)
mask_all = np.copy(base)

for N in range(1, analysis_range):
    for n in range(1, N):
        mask_all[N,n] = True

data_sigmoid = np.load('results/evaluation.sigmoid.transition_only.npy')
mask_transit = data_sigmoid != -1
mask_transit[:, analysis_range:] = False
mask_transit[analysis_range:,:] = False


for res in results_meta:
    data = np.load(res['res_path'])

    data_masked = data[mask_transit]
    mean_triangle, std_triangle = round(np.mean(data_masked), 3), round(np.std(data_masked), 3)

    print(f"{res['name']} - transit:\t\tmean:\t{mean_triangle}\tstd:\t{std_triangle}")

    if res['name'] == 'GA Sigmoid':
        continue

    data_masked = data[mask_all]
    mean_all, std_all = round(np.mean(data_masked), 3), round(np.std(data_masked), 3)
    print(f"{res['name']} - all:\t\tmean:\t{mean_all}\tstd:\t{std_all}")
