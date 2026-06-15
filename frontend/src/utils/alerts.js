import Swal from 'sweetalert2'
import 'sweetalert2/dist/sweetalert2.min.css'

const baseOptions = {
  background: '#0d0828',
  color: '#ffffff',
  confirmButtonColor: '#6f50ff',
  cancelButtonColor: '#312452',
  customClass: {
    popup: 'traffic-alert-popup',
    confirmButton: 'traffic-alert-confirm',
    cancelButton: 'traffic-alert-cancel',
  },
}

export function showSuccessToast(title = 'Cambios aplicados') {
  return Swal.fire({
    ...baseOptions,
    toast: true,
    position: 'top-end',
    icon: 'success',
    title,
    showConfirmButton: false,
    timer: 1800,
    timerProgressBar: true,
  })
}

export function showErrorAlert(title, text) {
  return Swal.fire({
    ...baseOptions,
    icon: 'error',
    title,
    text,
    confirmButtonText: 'Entendido',
  })
}

export function confirmLogout() {
  return Swal.fire({
    ...baseOptions,
    icon: 'warning',
    title: 'Cerrar sesion',
    text: 'Estas seguro que quieres cerrar sesion?',
    showCancelButton: true,
    confirmButtonText: 'Si, cerrar sesion',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
  })
}
