// Yoinked from Dynamo Onion Package https://github.com/maciekglowka/Onion


using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using Autodesk.Revit.DB;
using RevitServices.Transactions;
using RevitServices.Persistence;
using Revit.Elements;

using System.Windows;
using System.Windows.Forms;
using System.Drawing;
using System.Threading;

using System.Collections;
using Autodesk.DesignScript.Runtime;

namespace Onion
{
    public static class AutoJoin
    {
        private delegate void ProgressBarDelegate();
        private static ProgressBarForm pbForm;
        private static int progress;
        private static Options options;

        [MultiReturn(new[] { "element A", "element B" })]
        public static Dictionary<string, object> UnjoinNotIntersecting()
        {
            IList outputA = new List<object>();
            IList outputB = new List<object>();
            Document document = DocumentManager.Instance.CurrentDBDocument;
            IList<Autodesk.Revit.DB.FailureMessage> messages = document.GetWarnings();
            TransactionManager.Instance.EnsureInTransaction(document);

                foreach (Autodesk.Revit.DB.FailureMessage fm in messages)
                {
                    if (fm.GetFailureDefinitionId() == BuiltInFailures.JoinElementsFailures.JoiningDisjointWarn || fm.GetFailureDefinitionId() == BuiltInFailures.JoinElementsFailures.JoiningDisjoint)
                    {
                        List<ElementId> ids = fm.GetFailingElements().ToList();
                        if (ids.Count==2) try
                        {
                            Autodesk.Revit.DB.Element eA = document.GetElement(ids[0]);
                            Autodesk.Revit.DB.Element eB = document.GetElement(ids[1]);
                            JoinGeometryUtils.UnjoinGeometry(document, eA, eB);
                            outputA.Add(eA.ToDSType(true));
                            outputB.Add(eB.ToDSType(true));
                        }
                        catch (Autodesk.Revit.Exceptions.ApplicationException)
                        {
                        }
                    }
                }

            TransactionManager.Instance.TransactionTaskDone();
            return new Dictionary<string, object>
            {
                {"element A", outputA },
                {"element B", outputB }
            };
        }

        [MultiReturn(new[] { "element A", "element B" })]
        public static Dictionary<string, object> JoinList(List<Revit.Elements.Element> elementsA, List<Revit.Elements.Element> elementsB, double tolerance= 1.0e-09)
        {
            IList outputA = new List<object>();
            IList outputB = new List<object>();

            Document doc = DocumentManager.Instance.CurrentDBDocument;
            TransactionManager.Instance.EnsureInTransaction(doc);
            options = doc.Application.Create.NewGeometryOptions();

            using (pbForm = new ProgressBarForm())
            {
                pbForm.Show();

                double maxCount = elementsA.Count * elementsB.Count;
                progress = 0;

                for (int i = 0; i < elementsA.Count; i++)
                {
                    Autodesk.Revit.DB.Element eA = elementsA[i].InternalElement;
                    BoundingBoxXYZ bbA = eA.get_BoundingBox(null);
                    if (bbA != null)
                    {
                        for (int j = 0; j < elementsB.Count; j++)
                        {
                            progress = (int)(100 * (i * elementsB.Count + j) / maxCount);
                            pbForm.progressBar.Invoke(new ProgressBarDelegate(updateProgress));
                            Autodesk.Revit.DB.Element eB = elementsB[j].InternalElement;
                            BoundingBoxXYZ bbB = eB.get_BoundingBox(null);
                            if (eA != eB && bbB != null)
                            {
                                if (bbIntersect(bbA, bbB, tolerance))
                                {
                                    if (Utils.elementIntersect(eA, eB, options))
                                    {
                                        try
                                        {
                                            JoinGeometryUtils.JoinGeometry(doc, eA, eB);
                                            outputA.Add(elementsA[i]);
                                            outputB.Add(elementsB[j]);
                                        }
                                        catch (Autodesk.Revit.Exceptions.ApplicationException)
                                        {

                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                TransactionManager.Instance.TransactionTaskDone();
                pbForm.Close();
            }

            return new Dictionary<string, object>
            {
                {"element A", outputA },
                {"element B", outputB }
            };
        }

        private static void updateProgress()
        {
            pbForm.progressBar.Value = progress;
            pbForm.Text = progress.ToString() + "%";
        }

        private static bool overlap1D(double a1, double a2, double b1, double b2, double tolerance)
        {
            if (a2 + tolerance >= b1 && b2 + tolerance >= a1) return true;
            return false;
        }
        private static bool bbIntersect(BoundingBoxXYZ A, BoundingBoxXYZ B, double tolerance)
        {

            return overlap1D(A.Min.X, A.Max.X, B.Min.X, B.Max.X, tolerance) &&
              overlap1D(A.Min.Y, A.Max.Y, B.Min.Y, B.Max.Y, tolerance) &&
              overlap1D(A.Min.Z, A.Max.Z, B.Min.Z, B.Max.Z, tolerance);

        }

        private class ProgressBarForm : System.Windows.Forms.Form
        {
            public ProgressBar progressBar;
            public ProgressBarForm()
            {
                this.Width = 260;
                this.Height = 120;
                this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;

                progressBar = new ProgressBar();
                progressBar.Location = new System.Drawing.Point(20, 20);
                progressBar.Width = 200;
                progressBar.Height = 30;
                progressBar.Name = "Join Progress";
                progressBar.Minimum = 0;
                progressBar.Maximum = 100;
                progressBar.Value = 0;

                this.Controls.Add(progressBar);

            }

        }

    }
}