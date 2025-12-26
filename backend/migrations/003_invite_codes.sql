CREATE TABLE IF NOT EXISTS InviteCodes (
  InviteCodeId text PRIMARY KEY,
  InviteCode text NOT NULL,
  InviteEmail text NOT NULL,
  CreatedByUserId text NOT NULL,
  CreatedAt text NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UsedByUserId text,
  UsedAt text,
  RequireGmail integer NOT NULL DEFAULT 1,
  FOREIGN KEY (CreatedByUserId) REFERENCES Users(UserId),
  FOREIGN KEY (UsedByUserId) REFERENCES Users(UserId)
);

CREATE UNIQUE INDEX IF NOT EXISTS InviteCodes_Code_Ux ON InviteCodes (InviteCode);
CREATE UNIQUE INDEX IF NOT EXISTS InviteCodes_PendingEmail_Ux ON InviteCodes (InviteEmail) WHERE UsedAt IS NULL;
CREATE INDEX IF NOT EXISTS InviteCodes_CreatedBy_Idx ON InviteCodes (CreatedByUserId);
