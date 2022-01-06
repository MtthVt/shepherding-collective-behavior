import numpy as np

original_strombom_res_path = ''
ga_strombom_res_path = ''
ga_sigmoid_res_path = ''

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

base = np.zeros((140, 140), dtype=bool)
mask_all = np.copy(base)
mask_triangle = np.copy(base)

for N in range(1, mask_all.shape[0]):
    for n in range(1, N):
        mask_all[N,n] = True

for N in range(1, mask_triangle.shape[0]):
    for n in range(int(np.floor(3 * np.log2(N))), int(np.ceil(0.53 * N))):
        mask_triangle[N,n] = True


for res in results_meta:
    data = np.load(res['res_path'])

    data_masked = data[mask_triangle]
    mean_triangle, std_triangle = np.mean(data_masked), np.std(data_masked)

    print(f"{res['name']} - triangle:\n\tmean:\t{mean_triangle}\tstd:\t{std_triangle}")

    if res['name'] == 'GA Sigmoid':
        continue

    data_masked = data[mask_all]
    mean_all, std_all = np.mean(data_masked), np.std(data_masked)
    print(f"{res['name']} - all:\n\tmean:\t{mean_all}\tstd:\t{std_all}")
