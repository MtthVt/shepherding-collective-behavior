using UnityEngine;
using UnityEngine.SceneManagement;

public class BarnController : MonoBehaviour
{
  public ParticleSystem sheepCollectDustParticles;
  public ParticleSystem sheepCollectWheatParticles;

  [Header("GameManager GO")]
  public GameObject GMGO;

  private GameManager GM;

  // Use this for initialization
  void Start()
  {
    GM = GMGO.GetComponent<GameManager>();
  }

  void OnTriggerEnter(Collider other)
  {
    if (other.tag == "Sheep")
    {
      SheepController SC = other.gameObject.GetComponent<SheepController>();
      SC.dead = true;
      SC.gameObject.SetActive(false);

      GM.sheepCount--;
    }

    // Particles on entering the Barn
    sheepCollectDustParticles.transform.position = sheepCollectWheatParticles.transform.position = other.transform.position;

    sheepCollectDustParticles.Play();
    sheepCollectWheatParticles.Play();
  }
}
