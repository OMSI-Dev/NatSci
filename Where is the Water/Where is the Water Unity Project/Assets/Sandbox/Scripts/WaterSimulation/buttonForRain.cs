using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.InputSystem;

public class buttonForRain : MonoBehaviour
{
    bool buttonPressed = false;
    public GameObject rain;

    void Update()
    {

        if (Input.GetKey("down"))
        {
            if (!buttonPressed)
            {
                buttonPressed = true;
                rain.SetActive(true);
            }
            else if (buttonPressed)
            {
                buttonPressed = false;
                rain.SetActive(false);
            }
        }
    }
}

