import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import joblib

# Column names for NSL-KDD
columns = ['duration','protocol_type','service','flag','src_bytes','dst_bytes',
           'land','wrong_fragment','urgent','hot','num_failed_logins','logged_in',
           'num_compromised','root_shell','su_attempted','num_root','num_file_creations',
           'num_shells','num_access_files','num_outbound_cmds','is_host_login',
           'is_guest_login','count','srv_count','serror_rate','srv_serror_rate',
           'rerror_rate','srv_rerror_rate','same_srv_rate','diff_srv_rate',
           'srv_diff_host_rate','dst_host_count','dst_host_srv_count',
           'dst_host_same_srv_rate','dst_host_diff_srv_rate','dst_host_same_src_port_rate',
           'dst_host_srv_diff_host_rate','dst_host_serror_rate','dst_host_srv_serror_rate',
           'dst_host_rerror_rate','dst_host_srv_rerror_rate','label','difficulty']

# Load data
train_df = pd.read_csv('data/KDDTrain+.txt', names=columns, header=None)
test_df = pd.read_csv('data/KDDTest+.txt', names=columns, header=None)

# Map attack types to categories
attack_mapping = {
    'normal': 'Normal',
    'back': 'DoS', 'land': 'DoS', 'neptune': 'DoS', 'pod': 'DoS', 'smurf': 'DoS',
    'teardrop': 'DoS', 'mailbomb': 'DoS', 'apache2': 'DoS', 'processtable': 'DoS',
    'udpstorm': 'DoS', 'ipsweep': 'Probe', 'nmap': 'Probe', 'portsweep': 'Probe',
    'satan': 'Probe', 'mscan': 'Probe', 'saint': 'Probe', 'ftp_write': 'R2L',
    'guess_passwd': 'R2L', 'imap': 'R2L', 'multihop': 'R2L', 'phf': 'R2L',
    'spy': 'R2L', 'warezclient': 'R2L', 'warezmaster': 'R2L', 'sendmail': 'R2L',
    'named': 'R2L', 'snmpgetattack': 'R2L', 'snmpguess': 'R2L', 'xlock': 'R2L',
    'xsnoop': 'R2L', 'worm': 'R2L', 'buffer_overflow': 'U2R', 'loadmodule': 'U2R',
    'perl': 'U2R', 'rootkit': 'U2R', 'httptunnel': 'U2R', 'ps': 'U2R',
    'sqlattack': 'U2R', 'xterm': 'U2R'
}

train_df['attack_category'] = train_df['label'].map(attack_mapping)
test_df['attack_category'] = test_df['label'].map(attack_mapping)

# Remove difficulty column
train_df = train_df.drop('difficulty', axis=1)
test_df = test_df.drop('difficulty', axis=1)

# Categorical features
categorical = ['protocol_type', 'service', 'flag']

# One-hot encoding
train_encoded = pd.get_dummies(train_df, columns=categorical)
test_encoded = pd.get_dummies(test_df, columns=categorical)

# Align train and test columns
train_encoded, test_encoded = train_encoded.align(test_encoded, join='left', axis=1, fill_value=0)

# Separate features and labels
X_train = train_encoded.drop(['label', 'attack_category'], axis=1)
y_train = train_encoded['attack_category']
X_test = test_encoded.drop(['label', 'attack_category'], axis=1)
y_test = test_encoded['attack_category']

# Normalize numerical features
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Convert back to DataFrame
X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)

# Apply SMOTE (only on training data)
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

# Save preprocessed data and scaler
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(X_train.columns.tolist(), 'feature_names.pkl')
X_train_resampled.to_csv('X_train_processed.csv', index=False)
y_train_resampled.to_csv('y_train_processed.csv', index=False)
X_test_scaled.to_csv('X_test_processed.csv', index=False)
y_test.to_csv('y_test_processed.csv', index=False)

print(f"Training samples after SMOTE: {X_train_resampled.shape}")
print(f"Test samples: {X_test_scaled.shape}")
print(f"Class distribution:\n{y_train_resampled.value_counts()}")
