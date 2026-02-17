using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// Script to adjust the square / bounding square for the sandbox.
// Hit "h" to show the square, hit "m" to enable moving the square, hit "h" to enable changing the square size.
// when "n" is enabled, circle will follow position of the mouse translated to the world position
// when "a" is enabled, circle will change size with the up and down arrows
// Hit "n" again to stop moving the square, hit "a" to hide the square.
// Will actually end up being an ellipse since the radius x and y are adjustable separately.

public class SquareTest : MonoBehaviour
{
    public GameObject testSquare;
    public bool showSquare = false;
    public bool moveSquare = false;
    public bool changeSquareSize = false;

    private int constZ = 25;

    void Start()
    {
        if (!showSquare)
        {
            testSquare.SetActive(false);
        }
        float x = PlayerPrefs.GetFloat("CirclePositionX");
        float y = PlayerPrefs.GetFloat("CirclePositionY");

        testSquare.transform.position = new Vector3(x, y, constZ);

        float scaleX = PlayerPrefs.GetFloat("CircleScaleX");
        float scaleY = PlayerPrefs.GetFloat("CircleScaleY");

        if (scaleX == 0 || scaleY == 0)
        {
            testSquare.transform.localScale = new Vector3(50, 50, 1);
        }
        else
        {
            testSquare.transform.localScale = new Vector3(scaleX, scaleY, 1);
        }
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.H))
        {
            if (!showSquare)
            {
                testSquare.SetActive(true);
                showSquare = true;
            }
            else if (showSquare)
            {
                PlayerPrefs.SetFloat("SquarePositionX", testSquare.transform.position.x);
                PlayerPrefs.SetFloat("SquarePositionY", testSquare.transform.position.y);
                PlayerPrefs.SetFloat("SquareScaleX", testSquare.transform.localScale.x);
                PlayerPrefs.SetFloat("SquareScaleY", testSquare.transform.localScale.y);
                testSquare.SetActive(false);
                showSquare = false;
            }
        }

        // move the circle with the mouse
        if (showSquare)
        {
            if (Input.GetKeyDown(KeyCode.N))
            {
                if (!moveSquare)
                {
                    moveSquare = true;
                }
                else if (moveSquare)
                {
                    moveSquare = false;
                }
            }

            if (moveSquare)
            {
                Vector3 mousePos = Input.mousePosition;

                testSquare.transform.position = new Vector3(mousePos.x, mousePos.y, constZ);
            }

            if (Input.GetKeyDown(KeyCode.A))
            {
                if (!changeSquareSize)
                {
                    changeSquareSize = true;
                }
                else if (changeSquareSize)
                {
                    changeSquareSize = false;
                }
            }

            if (changeSquareSize)
            {
                float currentX = testSquare.transform.localScale.x;
                float currentY = testSquare.transform.localScale.y;

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

                testSquare.transform.localScale = new Vector3(currentX, currentY, 1);
            }
        }
    }

    public Vector3 GetPosition()
    {
        return testSquare.transform.position;
    }

    public Vector3 GetScale()
    {
        return testSquare.transform.localScale;
    }

    public Bounds GetBounds()
    {
        return testSquare.GetComponent<Renderer>().bounds;
    }

    public bool EditingSquare()
    {
        return showSquare;
    }
}
