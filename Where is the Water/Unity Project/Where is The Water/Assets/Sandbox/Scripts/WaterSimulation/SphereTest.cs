using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// Script to adjust the sphere / bounding circle for the sandbox.
// Hit "c" to show the sphere, hit "m" to enable moving the sphere, hit "s" to enable changing the sphere size.
// when "m" is enabled, circle will follow position of the mouse translated to the world position
// when "s" is enabled, circle will change size with the up and down arrows
// Hit "m" again to stop moving the sphere, hit "c" to hide the sphere.
// Will actually end up being an ellipse since the radius x and y are adjustable separately.

public class SphereTest : MonoBehaviour
{
    public GameObject testSphere;

    public bool showSphere = false;
    public bool moveSphere = false;
    public bool changeSphereSize = false;

    private int constZ = 25;

    void Start()
    {
        if (!showSphere)
        {
            testSphere.SetActive(false);
        }
        float x = PlayerPrefs.GetFloat("CirclePositionX");
        float y = PlayerPrefs.GetFloat("CirclePositionY");

        testSphere.transform.position = new Vector3(x, y, constZ);

        float scaleX = PlayerPrefs.GetFloat("CircleScaleX");
        float scaleY = PlayerPrefs.GetFloat("CircleScaleY");

        if (scaleX == 0 || scaleY == 0)
        {
            testSphere.transform.localScale = new Vector3(50, 50, 1);
        }
        else
        {
            testSphere.transform.localScale = new Vector3(scaleX, scaleY, 1);
        }
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.C))
        {
            if (!showSphere)
            {
                testSphere.SetActive(true);
                showSphere = true;
            }
            else if (showSphere)
            {
                PlayerPrefs.SetFloat("CirclePositionX", testSphere.transform.position.x);
                PlayerPrefs.SetFloat("CirclePositionY", testSphere.transform.position.y);
                PlayerPrefs.SetFloat("CircleScaleX", testSphere.transform.localScale.x);
                PlayerPrefs.SetFloat("CircleScaleY", testSphere.transform.localScale.y);
                testSphere.SetActive(false);
                showSphere = false;
            }
        }

        // move the circle with the mouse
        if (showSphere)
        {
            if (Input.GetKeyDown(KeyCode.M))
            {
                if (!moveSphere)
                {
                    moveSphere = true;
                }
                else if (moveSphere)
                {
                    moveSphere = false;
                }
            }

            if (moveSphere)
            {
                Vector3 mousePos = Input.mousePosition;

                testSphere.transform.position = new Vector3(mousePos.x, mousePos.y, constZ);
            }

            if (Input.GetKeyDown(KeyCode.S))
            {
                if (!changeSphereSize)
                {
                    changeSphereSize = true;
                }
                else if (changeSphereSize)
                {
                    changeSphereSize = false;
                }
            }

            if (changeSphereSize)
            {
                float currentX = testSphere.transform.localScale.x;
                float currentY = testSphere.transform.localScale.y;

                if (Input.GetKeyDown(KeyCode.UpArrow))
                {
                    currentY++;
                }
                if (Input.GetKeyDown(KeyCode.DownArrow))
                {
                    currentY--;
                }
                if (Input.GetKeyDown(KeyCode.RightArrow))
                {
                    currentX++;
                }
                if (Input.GetKeyDown(KeyCode.LeftArrow))
                {
                    currentX--;
                }

                testSphere.transform.localScale = new Vector3(currentX, currentY, 1);
            }
        }
    }

    public Vector3 GetPosition()
    {
        return testSphere.transform.position;
    }

    public Vector3 GetScale()
    {
        return testSphere.transform.localScale;
    }

    public bool EditingCircle()
    {
        return showSphere;
    }
}
