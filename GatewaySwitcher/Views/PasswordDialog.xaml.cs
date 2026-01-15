using System.Windows;
using System.Windows.Input;

namespace GatewaySwitcher.Views
{
    /// <summary>
    /// Dialog for entering password to update default profile
    /// </summary>
    public partial class PasswordDialog : Window
    {
        public string Password => PasswordBox.Password;

        public PasswordDialog()
        {
            InitializeComponent();
            Loaded += (s, e) => PasswordBox.Focus();
        }

        private void Confirm_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(PasswordBox.Password))
            {
                ErrorText.Text = "Please enter a password";
                ErrorText.Visibility = Visibility.Visible;
                PasswordBox.Focus();
                return;
            }

            DialogResult = true;
            Close();
        }

        private void Cancel_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }

        private void PasswordBox_KeyDown(object sender, KeyEventArgs e)
        {
            // Hide error when typing
            ErrorText.Visibility = Visibility.Collapsed;

            if (e.Key == Key.Enter)
            {
                Confirm_Click(sender, e);
            }
            else if (e.Key == Key.Escape)
            {
                Cancel_Click(sender, e);
            }
        }
    }
}
