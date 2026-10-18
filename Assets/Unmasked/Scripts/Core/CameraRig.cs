using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// Third-person orbit camera for the local player's pawn. Pawns read Yaw to move relative to the
    /// view. Also plays the unmask shot when the Haunter is caught.
    /// </summary>
    public class CameraRig : MonoBehaviour
    {
        public static CameraRig Instance { get; private set; }

        public float Distance = 4f;
        public float Height = 1.6f;
        public float MouseSensitivity = 0.12f;
        public float MinPitch = -40f;
        public float MaxPitch = 70f;

        public Transform Target { get; private set; }
        public float Yaw { get; private set; }
        public float Pitch { get; private set; } = 15f;

        /// <summary>Chase cam (driving the van): the view swings round behind the target.</summary>
        public bool Chase { get; set; }

        /// <summary>True while a menu (the Suspect Board, the town map) has the mouse.</summary>
        public bool InputLocked { get; set; }

        Vector3 unmaskFocus;
        float unmaskUntil;

        void Awake() => Instance = this;

        public void SetTarget(Transform target, float distance)
        {
            Target = target;
            Distance = distance;
            Height = 1.6f;
            Chase = false;
            if (target != null) Yaw = target.eulerAngles.y;
        }

        /// <summary>Follow something bigger than a person (the van), optionally as a chase cam.</summary>
        public void Follow(Transform target, float distance, float height, bool chase)
        {
            SetTarget(target, distance);
            Height = height;
            Chase = chase;
            Pitch = 14f;
        }

        public Vector3 AimDirection => Quaternion.Euler(Pitch, Yaw, 0f) * Vector3.forward;

        public void PlayUnmask(Vector3 focus, float duration)
        {
            unmaskFocus = focus;
            unmaskUntil = Time.time + duration;
        }

        void LateUpdate()
        {
            bool cursorFree = InputLocked || Cursor.lockState != CursorLockMode.Locked;
            if (!cursorFree && Mouse.current != null)
            {
                Vector2 delta = Mouse.current.delta.ReadValue() * MouseSensitivity;
                Yaw += delta.x;
                Pitch = Mathf.Clamp(Pitch - delta.y, MinPitch, MaxPitch);
            }

            if (Time.time < unmaskUntil)
            {
                // The big reveal: slow orbit around the caught Haunter.
                float angle = (unmaskUntil - Time.time) * 15f;
                Vector3 offset = Quaternion.Euler(0f, angle, 0f) * new Vector3(0f, 1.2f, 3.2f);
                transform.position = Vector3.Lerp(transform.position, unmaskFocus + offset, Time.deltaTime * 3f);
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(unmaskFocus + Vector3.up - transform.position), Time.deltaTime * 4f);
                return;
            }

            if (Target == null) return;
            if (Chase) Yaw = Mathf.LerpAngle(Yaw, Target.eulerAngles.y, Time.deltaTime * 2.5f);

            Vector3 pivot = Target.position + Vector3.up * Height;
            Quaternion rotation = Quaternion.Euler(Pitch, Yaw, 0f);
            float distance = Distance;
            if (Physics.SphereCast(pivot, 0.2f, rotation * Vector3.back, out var hit, Distance, ~0, QueryTriggerInteraction.Ignore)
                && hit.transform.root != Target.root)
            {
                distance = Mathf.Max(0.5f, hit.distance - 0.1f);
            }
            transform.SetPositionAndRotation(pivot + rotation * Vector3.back * distance + rotation * new Vector3(0.5f, 0f, 0f), rotation);
        }
    }
}
